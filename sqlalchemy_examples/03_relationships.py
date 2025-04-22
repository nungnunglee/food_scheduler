"""
03_relationships.py - SQLAlchemy 관계 모델링 예제

이 파일은 다음 내용을 다룹니다:
1. 일대다(One-to-Many) 관계
2. 다대다(Many-to-Many) 관계
3. 일대일(One-to-One) 관계
4. 자기 참조(Self-referential) 관계

관계형 데이터베이스의 핵심 기능인 테이블 간 관계를 SQLAlchemy로 구현하는 방법을 보여줍니다.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import datetime

# --- 데이터베이스 연결 설정 ---
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "myappdb")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 다대다 관계를 위한 연결 테이블 정의 ---
# 학생과 과목 간의 다대다 관계 매핑
student_course = Table(
    'student_course',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

# --- 1. 일대다(One-to-Many) 관계 모델 ---
class Department(Base):
    """학과 정보 (일대다 관계의 '일' 쪽)"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    
    # relationship 정의: 학과에 속한 모든 교수들
    # 역참조: Professor 모델의 department 속성
    professors = relationship("Professor", back_populates="department")
    
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"

class Professor(Base):
    """교수 정보 (일대다 관계의 '다' 쪽)"""
    __tablename__ = 'professors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    
    # 외래 키: 소속 학과 ID
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    
    # relationship 정의: 소속 학과 정보
    # 역참조: Department 모델의 professors 속성
    department = relationship("Department", back_populates="professors")
    
    # relationship 정의: 교수가 가르치는 과목들
    # 역참조: Course 모델의 professor 속성
    courses = relationship("Course", back_populates="professor")
    
    def __repr__(self):
        return f"<Professor(id={self.id}, name='{self.name}', department_id={self.department_id})>"

# --- 2. 다대다(Many-to-Many) 관계 모델 ---
class Student(Base):
    """학생 정보 (다대다 관계)"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    
    # relationship 정의: 학생이 수강하는 과목들
    # secondary: 다대다 관계를 연결하는 중간 테이블
    # back_populates: Course 모델의 students 속성
    courses = relationship(
        "Course",
        secondary=student_course,
        back_populates="students"
    )
    
    # 일대일 관계: 학생 상세 정보
    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    
    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"

class Course(Base):
    """과목 정보 (다대다 및 일대다 관계)"""
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    
    # 외래 키: 강의하는 교수 ID (일대다 관계)
    professor_id = Column(Integer, ForeignKey('professors.id'), nullable=False)
    
    # relationship 정의: 강의하는 교수 정보
    professor = relationship("Professor", back_populates="courses")
    
    # relationship 정의: 과목을 수강하는 학생들
    students = relationship(
        "Student",
        secondary=student_course,
        back_populates="courses"
    )
    
    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', professor_id={self.professor_id})>"

# --- 3. 일대일(One-to-One) 관계 모델 ---
class StudentProfile(Base):
    """학생 상세 정보 (일대일 관계)"""
    __tablename__ = 'student_profiles'
    
    id = Column(Integer, primary_key=True)
    # 외래 키: 학생 ID (unique=True로 일대일 관계 보장)
    student_id = Column(Integer, ForeignKey('students.id'), unique=True, nullable=False)
    bio = Column(Text)
    birth_date = Column(DateTime)
    
    # relationship 정의: 해당 학생 정보
    student = relationship("Student", back_populates="profile")
    
    def __repr__(self):
        return f"<StudentProfile(id={self.id}, student_id={self.student_id})>"

# --- 4. 자기 참조(Self-referential) 관계 모델 ---
class Employee(Base):
    """직원 정보 (자기 참조 관계 - 조직도)"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    # 자기 참조 외래 키: 상사 ID
    manager_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    
    # relationship 정의: 상사 정보
    manager = relationship("Employee", remote_side=[id], backref="subordinates")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', manager_id={self.manager_id})>"

# --- 테이블 생성 및 샘플 데이터 ---
def create_tables_and_samples():
    """테이블 생성 및 샘플 데이터 추가"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as session:
        # 1. 학과 데이터 생성
        computer_science = Department(name="컴퓨터공학과")
        mathematics = Department(name="수학과")
        physics = Department(name="물리학과")
        
        session.add_all([computer_science, mathematics, physics])
        session.flush()  # ID 할당을 위해 flush
        
        # 2. 교수 데이터 생성
        prof_kim = Professor(name="김교수", department_id=computer_science.id)
        prof_lee = Professor(name="이교수", department_id=computer_science.id)
        prof_park = Professor(name="박교수", department_id=mathematics.id)
        
        session.add_all([prof_kim, prof_lee, prof_park])
        session.flush()
        
        # 3. 과목 데이터 생성
        course_python = Course(title="파이썬 프로그래밍", professor_id=prof_kim.id)
        course_database = Course(title="데이터베이스", professor_id=prof_kim.id)
        course_algorithm = Course(title="알고리즘", professor_id=prof_lee.id)
        course_calculus = Course(title="미적분학", professor_id=prof_park.id)
        
        session.add_all([course_python, course_database, course_algorithm, course_calculus])
        session.flush()
        
        # 4. 학생 데이터 생성
        student_choi = Student(name="최학생")
        student_jung = Student(name="정학생")
        student_hong = Student(name="홍학생")
        
        # 학생별 수강 과목 설정
        student_choi.courses = [course_python, course_database, course_algorithm]
        student_jung.courses = [course_python, course_calculus]
        student_hong.courses = [course_algorithm, course_calculus]
        
        session.add_all([student_choi, student_jung, student_hong])
        session.flush()
        
        # 5. 학생 프로필 정보 추가 (일대일 관계)
        profile_choi = StudentProfile(
            student_id=student_choi.id,
            bio="컴퓨터공학 전공 학생입니다.",
            birth_date=datetime.datetime(2000, 5, 15)
        )
        profile_jung = StudentProfile(
            student_id=student_jung.id,
            bio="수학과 복수전공 중입니다.",
            birth_date=datetime.datetime(1999, 8, 22)
        )
        
        session.add_all([profile_choi, profile_jung])
        
        # 6. 직원 데이터 생성 (자기 참조 관계)
        ceo = Employee(name="대표이사")
        cto = Employee(name="기술이사", manager_id=None)  # 나중에 업데이트
        team_lead1 = Employee(name="팀장1", manager_id=None)  # 나중에 업데이트
        team_lead2 = Employee(name="팀장2", manager_id=None)  # 나중에 업데이트
        
        session.add_all([ceo, cto, team_lead1, team_lead2])
        session.flush()
        
        # 매니저 관계 설정
        cto.manager_id = ceo.id
        team_lead1.manager_id = cto.id
        team_lead2.manager_id = cto.id
        
        dev1 = Employee(name="개발자1", manager_id=team_lead1.id)
        dev2 = Employee(name="개발자2", manager_id=team_lead1.id)
        designer = Employee(name="디자이너", manager_id=team_lead2.id)
        
        session.add_all([dev1, dev2, designer])
        
        # 모든 변경사항 커밋
        session.commit()
        print("샘플 데이터가 성공적으로 생성되었습니다.")

# --- 관계 쿼리 예제 함수 ---
def query_examples(session: Session):
    """다양한 관계 쿼리 사용 예제"""
    print("\n=== 1. 일대다 관계 쿼리 ===")
    # 학과별 소속 교수 조회
    dept = session.query(Department).filter_by(name="컴퓨터공학과").first()
    print(f"학과: {dept.name}")
    print("소속 교수:")
    for professor in dept.professors:
        print(f"- {professor.name}")
    
    # 교수가 가르치는 과목 조회
    professor = session.query(Professor).filter_by(name="김교수").first()
    print(f"\n교수: {professor.name} (소속: {professor.department.name})")
    print("강의 과목:")
    for course in professor.courses:
        print(f"- {course.title}")
    
    print("\n=== 2. 다대다 관계 쿼리 ===")
    # 학생이 수강하는 과목 조회
    student = session.query(Student).filter_by(name="최학생").first()
    print(f"학생: {student.name}")
    print("수강 과목:")
    for course in student.courses:
        print(f"- {course.title} (교수: {course.professor.name})")
    
    # 과목을 수강하는 학생 조회
    course = session.query(Course).filter_by(title="알고리즘").first()
    print(f"\n과목: {course.title} (교수: {course.professor.name})")
    print("수강 학생:")
    for student in course.students:
        print(f"- {student.name}")
    
    print("\n=== 3. 일대일 관계 쿼리 ===")
    # 학생과 프로필 정보 조회
    students = session.query(Student).all()
    for student in students:
        if student.profile:
            birth_date = student.profile.birth_date.strftime("%Y-%m-%d") if student.profile.birth_date else "정보 없음"
            print(f"{student.name} - 자기소개: {student.profile.bio}, 생년월일: {birth_date}")
        else:
            print(f"{student.name} - 프로필 정보 없음")
    
    print("\n=== 4. 자기 참조 관계 쿼리 ===")
    # 조직도 출력
    ceo = session.query(Employee).filter_by(manager_id=None).first()
    
    def print_org_chart(employee, level=0):
        indent = "  " * level
        print(f"{indent}- {employee.name}")
        for subordinate in employee.subordinates:
            print_org_chart(subordinate, level + 1)
    
    print("조직도:")
    print_org_chart(ceo)
    
    # 특정 직원의 상사 체인 출력
    dev = session.query(Employee).filter_by(name="개발자1").first()
    print(f"\n{dev.name}의 보고 라인:")
    current = dev
    while current.manager:
        print(f"{current.name} -> {current.manager.name}")
        current = current.manager

# --- 메인 코드 ---
if __name__ == "__main__":
    # 테이블 생성 및 샘플 데이터 추가
    print("=== 테이블 생성 및 샘플 데이터 추가 ===")
    create_tables_and_samples()
    
    # 관계 쿼리 예제 실행
    print("\n=== 관계 쿼리 예제 ===")
    with SessionLocal() as session:
        query_examples(session)

"""
실행 결과 예시:

=== 테이블 생성 및 샘플 데이터 추가 ===
2023-04-12 12:34:56,789 INFO sqlalchemy.engine.Engine CREATE TABLE departments (...)
...
샘플 데이터가 성공적으로 생성되었습니다.

=== 관계 쿼리 예제 ===

=== 1. 일대다 관계 쿼리 ===
학과: 컴퓨터공학과
소속 교수:
- 김교수
- 이교수

교수: 김교수 (소속: 컴퓨터공학과)
강의 과목:
- 파이썬 프로그래밍
- 데이터베이스

=== 2. 다대다 관계 쿼리 ===
학생: 최학생
수강 과목:
- 파이썬 프로그래밍 (교수: 김교수)
- 데이터베이스 (교수: 김교수)
- 알고리즘 (교수: 이교수)

과목: 알고리즘 (교수: 이교수)
수강 학생:
- 최학생
- 홍학생

=== 3. 일대일 관계 쿼리 ===
최학생 - 자기소개: 컴퓨터공학 전공 학생입니다., 생년월일: 2000-05-15
정학생 - 자기소개: 수학과 복수전공 중입니다., 생년월일: 1999-08-22
홍학생 - 프로필 정보 없음

=== 4. 자기 참조 관계 쿼리 ===
조직도:
- 대표이사
  - 기술이사
    - 팀장1
      - 개발자1
      - 개발자2
    - 팀장2
      - 디자이너

개발자1의 보고 라인:
개발자1 -> 팀장1
팀장1 -> 기술이사
기술이사 -> 대표이사
""" 