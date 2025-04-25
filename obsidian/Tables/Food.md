
| csv_name  | attr_name                | type         | ex                                  |
| --------- | ------------------------ | ------------ | ----------------------------------- |
| 식품코드      | food_id (PK)             | varchar(30)  | D101-004160000-0001                 |
| 식품명       | food_name (Not Null)     | varchar(50)  | 국밥_돼지머리                             |
| 데이터구분코드   | data_type_code           | char(1)      | D                                   |
| 식품기원코드    | origin_code              | int          | 1                                   |
| 식품대분류코드   | major_category_code      | int          | 01                                  |
| 대표식품코드    | representative_food_code | int          | 01004                               |
| 식품중분류코드   | medium_category_code     | int          | 0100416                             |
| 식품소분류코드   | minor_category_code      | int          | 010041600                           |
| 식품세분류코드   | detail_category_code     | int          | 00                                  |
| 출처코드      | source_code              | int          | 3                                   |
| 품목제조보고번호  | mfg_report_no            | int          | 20130405045594                      |
| 업체명       | company_name             | varchar(100) | 스타벅스                                |
| 제조사명      | manufacturer_name        | varchar(100) | 에쓰푸드(주)음성공장                         |
| 수입업체명     | importer_name            | varchar(100) | Yantai Longxiang Foodstuff Co.,LTD. |
| 유통업체명     | distributor_name         | varchar(100) | ㈜마이비                                |
| 수입여부      | is_imported              | char(1)      | Y                                   |
| 원산지국코드    | origin_country_code      | int          | 840                                 |
| 원산지국명     | origin_country_name      | varchar(10)  | 미국                                  |
| 데이터생성방법코드 | generation_method_code   | int          | 1                                   |
| 데이터기준일자   | reference_date           | date         | 2025-04-08                          |
| 제공기관코드    | provider_code            | int          | 1471000                             |
| 제공기관명     | provider_name            | varchar(50)  | 식품의약품안전처                            |
| 폐기율(%)    | disposal_rate_pct        | decimal(5,2) | 16                                  |
