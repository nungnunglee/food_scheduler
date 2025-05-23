from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from db.database import Base


__all__ = [
    "UserInfo",
    "UserAuth",
    "SocialLogin",
    "Password",
    "Subscription",
    "LoginLog",
    "UserBody",
    "UserSchedule",
    "UserFoodInventory",
]

class UserInfo(Base):
    __tablename__ = "user_info"

    uuid = Column(String(36), primary_key=True, index=True)
    nickname = Column(String(50))

    user_auth = relationship("UserAuth", uselist=False, back_populates="user_info")
    user_body = relationship("UserBody", uselist=False, back_populates="user_info")
    social_login = relationship("SocialLogin", uselist=False, back_populates="user_info")
    password = relationship("Password", uselist=False, back_populates="user_info")
    subscription = relationship("Subscription", uselist=False, back_populates="user_info")
    login_logs = relationship("LoginLog", back_populates="user_info")
    user_schedule = relationship("UserSchedule", back_populates="user_info")
    food_inventory = relationship("UserFoodInventory", back_populates="user_info")

class UserAuth(Base):
    __tablename__ = "user_auth"

    uuid = Column(String(36), ForeignKey("user_info.uuid"), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20), unique=True, index=True)

    user_info = relationship("UserInfo", uselist=False, back_populates="user_auth")

# Social_login 테이블 모델
class SocialLogin(Base):
    __tablename__ = "social_login"

    uuid = Column(String(36), ForeignKey("user_info.uuid"), primary_key=True, index=True)
    social_code = Column(String(20))
    access_token = Column(String(255))
    update_date = Column(DateTime, default=func.now(), onupdate=func.now())

    user_info = relationship("UserInfo", uselist=False, back_populates="social_login")

# Password 테이블 모델
class Password(Base):
    __tablename__ = "password"

    uuid = Column(String(36), ForeignKey("user_info.uuid"), primary_key=True, index=True)
    password = Column(String(255))
    update_date = Column(DateTime, default=func.now(), onupdate=func.now())

    user_info = relationship("UserInfo", uselist=False, back_populates="password")

# subscription 테이블 모델
class Subscription(Base):
    __tablename__ = "subscription"

    uuid = Column(String(36), ForeignKey("user_info.uuid"), primary_key=True, index=True)
    plan = Column(String(50))
    purchase = Column(DateTime)
    expired = Column(DateTime)

    user_info = relationship("UserInfo", uselist=False, back_populates="subscription")

class LoginLog(Base):
    __tablename__ = "login_log"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), ForeignKey("user_info.uuid"), index=True)
    status_code = Column(Integer)
    ip = Column(String(45))
    datetime = Column(DateTime, default=func.now())

    user_info = relationship("UserInfo", uselist=False, back_populates="login_logs")

class UserBody(Base):
    __tablename__ = "user_body"

    uuid = Column(String(36), ForeignKey("user_info.uuid"), primary_key=True, index=True)
    age = Column(Integer)
    tall = Column(Float)
    weight = Column(Float)
    sleep_pattern = Column(String(50))
    activity = Column(String(50))

    user_info = relationship("UserInfo", uselist=False, back_populates="user_body")

class UserSchedule(Base):
    __tablename__ = "user_schedule"
    __table_args__ = (
        PrimaryKeyConstraint('uuid', 'datetime'),
    )

    uuid = Column(String(36), ForeignKey("user_info.uuid"), index=True)
    datetime = Column(DateTime, default=func.now())
    food_name = Column(String(255), nullable=False)
    food_id = Column(String(30), ForeignKey("food_info.food_id"))

    user_info = relationship("UserInfo", uselist=False, back_populates="user_schedule")

class UserFoodInventory(Base):
    __tablename__ = "user_food_inventory"
    __table_args__ = (
        PrimaryKeyConstraint('uuid', 'food_id'),
    )

    uuid = Column(String(36), ForeignKey("user_info.uuid"), index=True)
    food_id = Column(String(19), ForeignKey("food_info.food_id"), index=True)
    quantity = Column(String(500), nullable=False)
    expired = Column(DateTime)

    user_info = relationship("UserInfo", uselist=False, back_populates="food_inventory")
