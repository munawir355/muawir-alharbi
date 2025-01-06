# user_service.py
from fastapi import HTTPException, status
import pyodbc
from typing import Optional, Dict


class UserService:
    @staticmethod
    async def get_user_by_email(conn: pyodbc.Connection, email: str) -> Optional[Dict]:
        """Get user from database by email"""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UserID, Name, Email FROM CW1.[User] WHERE Email = ?",
            email
        )
        row = cursor.fetchone()
        if row:
            return {
                "user_id": row[0],
                "name": row[1],
                "email": row[2]
            }
        return None

    @staticmethod
    async def create_user(conn: pyodbc.Connection, email: str, name: str) -> Dict:
        """Create new user in database"""
        cursor = conn.cursor()
        try:
            # Get the next available UserID
            cursor.execute("SELECT MAX(UserID) FROM CW1.[User]")
            max_id = cursor.fetchone()[0]
            new_id = 1 if max_id is None else max_id + 1

            # Insert new user
            cursor.execute(
                """
                INSERT INTO CW1.[User] (UserID, Name, Email, Password) 
                VALUES (?, ?, ?, 'external_auth')
                """,
                new_id, name, email
            )
            conn.commit()

            return {
                "user_id": new_id,
                "name": name,
                "email": email
            }
        except pyodbc.Error as e:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )

    @staticmethod
    async def get_or_create_user(
            conn: pyodbc.Connection,
            email: str,
            extract_name_from_email: bool = True
    ) -> Dict:
        """Get existing user or create new one"""
        user = await UserService.get_user_by_email(conn, email)

        if user is None:
            # Extract name from email for new users
            name = email.split('@')[0] if extract_name_from_email else email
            user = await UserService.create_user(conn, email, name)

        return user
