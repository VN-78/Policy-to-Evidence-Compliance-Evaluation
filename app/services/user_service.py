from app.models.users import UserCreate, UserResponse


class UserService:
    def __init__(self):
        # In a real app, you would inject your database session here
        self.fake_db: list[UserResponse] = []
        self.current_id = 1

    def create_user(self, user_in: UserCreate) -> UserResponse:
        # 1. Business logic (e.g., check if email already exists)
        for existing_user in self.fake_db:
            if existing_user.email == user_in.email:
                raise ValueError("Email already registered")

        # 2. Create the new user record
        new_user = UserResponse(
            id=self.current_id,
            username=user_in.username,
            email=user_in.email
        )
        
        # 3. "Save" to database
        self.fake_db.append(new_user)
        self.current_id += 1
        
        return new_user