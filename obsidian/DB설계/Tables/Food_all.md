
| csv_name     | attr_name                   | type          | ex                                  |
| ------------ | --------------------------- | ------------- | ----------------------------------- |
| 식품코드         | food_id (PK)                | varchar(19)   | D101-004160000-0001                 |
| 식품명          | food_name (Not Null)        | varchar(50)   | 국밥_돼지머리                             |
| 데이터구분코드      | data_type_code              | char(1)       | D                                   |
| 데이터구분명       | data_type_name              | varchar(50)   | 음식                                  |
| 식품기원코드       | origin_code                 | int           | 1                                   |
| 식품기원명        | origin_name                 | varchar(50)   | 가정식(분석 함량)                          |
| 식품대분류코드      | major_category_code         | int           | 01                                  |
| 식품대분류명       | major_category_name         | varchar(50)   | 밥류                                  |
| 대표식품코드       | representative_food_code    | int           | 01004                               |
| 대표식품명        | representative_food_name    | varchar(50)   | 국밥                                  |
| 식품중분류코드      | medium_category_code        | int           | 0100416                             |
| 식품중분류명       | medium_category_name        | varchar(50)   | 돼지머리                                |
| 식품소분류코드      | minor_category_code         | int           | 010041600                           |
| 식품소분류명       | minor_category_name         | varchar(50)   | 발효소시지                               |
| 식품세분류코드      | detail_category_code        | int           | 00                                  |
| 식품세분류명       | detail_category_name        | varchar(50)   | 생것                                  |
| 출처코드         | source_code                 | int           | 3                                   |
| 출처명          | source_name                 | varchar(100)  | 식품의약품안전처                            |
| 품목제조보고번호     | mfg_report_no               | int           | 2.01304E+13                         |
| 업체명          | company_name                | varchar(100)  | 스타벅스                                |
| 제조사명         | manufacturer_name           | varchar(100)  | 에쓰푸드(주)음성공장                         |
| 수입업체명        | importer_name               | varchar(100)  | Yantai Longxiang Foodstuff Co.,LTD. |
| 유통업체명        | distributor_name            | varchar(100)  | ㈜마이비                                |
| 수입여부         | is_imported                 | char(1)       | Y                                   |
| 원산지국코드       | origin_country_code         | int           | 840                                 |
| 원산지국명        | origin_country_name         | varchar(10)   | 미국                                  |
| 데이터생성방법코드    | generation_method_code      | int           | 1                                   |
| 데이터생성방법명     | generation_method_name      | varchar(10)   | 분석                                  |
| 데이터기준일자      | reference_date              | date          | 2025-04-08                          |
| 폐기율(%)       | disposal_rate_pct           | decimal(5,2)  | 16                                  |
| 식품중량         | weight                      | varchar(10)   | 900g                                |
| 1회 섭취참고량     | serving_size_g              | varchar(10)   | 30g                                 |
| 영양성분함량기준량    | nutrient_reference_amount_g | varchar(10)   | 100g                                |
| 에너지(kcal)    | energy_kcal                 | decimal(10,3) | 260                                 |
| 수분(g)        | moisture_g                  | decimal(10,3) | 56.8                                |
| 단백질(g)       | protein_g                   | decimal(10,3) | 21.24                               |
| 지방(g)        | fat_g                       | decimal(10,3) | 17.87                               |
| 회분(g)        | ash_g                       | decimal(10,3) | 0.53                                |
| 탄수화물(g)      | carbohydrate_g              | decimal(10,3) | 3.58                                |
| 당류(g)        | sugars_g                    | decimal(10,3) | 0.31                                |
| 식이섬유(g)      | dietary_fiber_g             | decimal(10,3) | 0                                   |
| 칼슘(mg)       | calcium_mg                  | decimal(10,3) | 6                                   |
| 철(mg)        | iron_mg                     | decimal(10,3) | 0.84                                |
| 인(mg)        | phosphorus_mg               | decimal(10,3) | 89                                  |
| 칼륨(mg)       | potassium_mg                | decimal(10,3) | 58                                  |
| 나트륨(mg)      | sodium_mg                   | decimal(10,3) | 177                                 |
| 비타민A(μg RAE) | vitamin_a_ug_rae            | decimal(10,3) | 3                                   |
| 레티놀(μg)      | retinol_ug                  | decimal(10,3) | 3                                   |
| 베타카로틴(μg)    | beta_carotene_ug            | decimal(10,3) | 0                                   |
| 티아민(mg)      | thiamin_mg                  | decimal(10,3) | 0.192                               |
| 리보플라빈(mg)    | riboflavin_mg               | decimal(10,3) | 0.065                               |
| 니아신(mg)      | niacin_mg                   | decimal(10,3) | 0.992                               |
| 비타민 C(mg)    | vitamin_c_mg                | decimal(10,3) | 7.88                                |
| 비타민 D(μg)    | vitamin_d_ug                | decimal(10,3) | 0                                   |
| 콜레스테롤(mg)    | cholesterol_mg              | decimal(10,3) | 64.41                               |
| 포화지방산(g)     | saturated_fat_g             | decimal(10,3) | 6.5                                 |
| 트랜스지방산(g)    | trans_fat_g                 | decimal(10,3) | 0.07                                |
