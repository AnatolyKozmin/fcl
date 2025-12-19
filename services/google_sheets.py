import gspread
from google.oauth2.service_account import Credentials
from typing import Optional
from database.models import User


class GoogleSheetsService:
    f'''Класс для работы с гугл щитс, всё что происходит при взаимодействии с их API делается строго через них'''

 
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    

    def __init__(self, credentials_file: str, spreadsheet_id: str):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
    

    def _get_client(self) -> gspread.Client:
        if not self._client:
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client
    

    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        if not self._spreadsheet:
            client = self._get_client()
            self._spreadsheet = client.open_by_key(self.spreadsheet_id)
        return self._spreadsheet
    

    def _get_or_create_worksheet(self, title: str, rows: int = 1000, cols: int = 15) -> gspread.Worksheet:
        spreadsheet = self._get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
        return worksheet
    

    async def export_registrations(self, users: list[User]) -> None:
        """Export all registrations to the main sheet"""
        worksheet = self._get_or_create_worksheet("Регистрации")
        

        worksheet.clear()

        
        headers = [
            "ID", "Telegram ID", "Username", "ФИО", "Группа",
            "Курс", "Факультет", "ВКонтакте", "Telegram",
            "Телефон", "Источник", "Статус", "Дата регистрации"
        ]
        

        data = [headers]
        for user in users:
            data.append([
                user.id,
                user.telegram_id,
                user.username or "",
                user.full_name,
                user.study_group,
                user.course,
                user.faculty,
                user.vk_link,
                user.tg_link,
                user.phone,
                user.source,
                user.status.value,
                user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])


        worksheet.update(data, "A1")
        worksheet.format("A1:M1", {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })
    

    async def export_confirmations(
        self,
        confirmed: list[User],
        declined: list[User] 
    ) -> None:
        

        worksheet = self._get_or_create_worksheet("Подтверждения")

        worksheet.clear()
        headers = ["ФИО", "Группа", "Курс", "Факультет", "Телефон", "Статус"]
        data = [headers]
        
 
        for user in confirmed:
            data.append([
                user.full_name,
                user.study_group,
                user.course,
                user.faculty,
                user.phone,
                "✅ Придёт"
            ])
        

        for user in declined:
            data.append([
                user.full_name,
                user.study_group,
                user.course,
                user.faculty,
                user.phone,
                "❌ Не придёт"
            ])

        worksheet.update(data, "A1")
        

        worksheet.format("A1:F1", {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })


        if confirmed:
            confirmed_range = f"A2:F{1 + len(confirmed)}"
            worksheet.format(confirmed_range, {
                "backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.85}
            })
        

        if declined:
            declined_start = 2 + len(confirmed)
            declined_end = declined_start + len(declined) - 1
            declined_range = f"A{declined_start}:F{declined_end}"
            worksheet.format(declined_range, {
                "backgroundColor": {"red": 0.95, "green": 0.85, "blue": 0.85}
            })

