-- HR Attrition & Compensation Analysis
-- Dataset: IBM HR Analytics Employee Attrition (1,470 employees, data/HR.csv)
-- Dialect: MySQL 8 (also runs unchanged on SQLite 3.25+ and PostgreSQL)
-- Table: hr_employees, loaded 1:1 from data/HR.csv

-- ============================================================
-- 0. Data quality checks
-- ============================================================

-- 0.1 Row count, unique IDs, nulls in key columns
SELECT COUNT(*)                                   AS total_rows,
       COUNT(DISTINCT EmployeeNumber)             AS unique_employees,
       SUM(CASE WHEN MonthlyIncome IS NULL THEN 1 ELSE 0 END) AS null_income,
       SUM(CASE WHEN Attrition IS NULL THEN 1 ELSE 0 END)     AS null_attrition
FROM hr_employees;

-- 0.2 Constant columns (one distinct value = no information, dropped in Power Query)
SELECT COUNT(DISTINCT EmployeeCount) AS employee_count_values,
       COUNT(DISTINCT Over18)        AS over18_values,
       COUNT(DISTINCT StandardHours) AS standard_hours_values
FROM hr_employees;

-- ============================================================
-- 1. Headline KPIs
-- ============================================================

-- 1.1 Headcount, leavers, attrition rate, averages
SELECT COUNT(*)                                                   AS employees,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)         AS leavers,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct,
       ROUND(AVG(MonthlyIncome), 0)                               AS avg_monthly_income,
       ROUND(AVG(Age), 1)                                         AS avg_age,
       ROUND(AVG(YearsAtCompany), 1)                              AS avg_tenure_years
FROM hr_employees;

-- ============================================================
-- 2. Where does attrition happen?
-- ============================================================

-- 2.1 Attrition by department
SELECT Department,
       COUNT(*)                                                   AS employees,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)         AS leavers,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees
GROUP BY Department
ORDER BY attrition_rate_pct DESC;

-- 2.2 Attrition by job role, ranked, with each role's share of all leavers
WITH role_stats AS (
    SELECT JobRole,
           COUNT(*)                                           AS employees,
           SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) AS leavers
    FROM hr_employees
    GROUP BY JobRole
)
SELECT JobRole,
       employees,
       leavers,
       ROUND(100.0 * leavers / employees, 1)                      AS attrition_rate_pct,
       ROUND(100.0 * leavers / SUM(leavers) OVER (), 1)           AS share_of_all_leavers_pct,
       RANK() OVER (ORDER BY 1.0 * leavers / employees DESC)      AS risk_rank
FROM role_stats
ORDER BY risk_rank;

-- 2.3 Attrition by age band
SELECT CASE WHEN Age <= 25 THEN '18-25'
            WHEN Age <= 35 THEN '26-35'
            WHEN Age <= 45 THEN '36-45'
            WHEN Age <= 55 THEN '46-55'
            ELSE '56+' END                                        AS age_band,
       COUNT(*)                                                   AS employees,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees
GROUP BY 1
ORDER BY 1;

-- 2.4 Attrition by tenure band (are new joiners the problem?)
SELECT CASE WHEN YearsAtCompany <= 2  THEN '1) 0-2 yrs'
            WHEN YearsAtCompany <= 5  THEN '2) 3-5 yrs'
            WHEN YearsAtCompany <= 10 THEN '3) 6-10 yrs'
            ELSE '4) 10+ yrs' END                                 AS tenure_band,
       COUNT(*)                                                   AS employees,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)         AS leavers,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees
GROUP BY 1
ORDER BY 1;

-- ============================================================
-- 3. Why do people leave? (drivers)
-- ============================================================

-- 3.1 Overtime vs no overtime, and the multiple between them
WITH ot AS (
    SELECT OverTime,
           AVG(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END) AS rate
    FROM hr_employees
    GROUP BY OverTime
)
SELECT ROUND(100 * MAX(CASE WHEN OverTime = 'Yes' THEN rate END), 1) AS overtime_rate_pct,
       ROUND(100 * MAX(CASE WHEN OverTime = 'No'  THEN rate END), 1) AS no_overtime_rate_pct,
       ROUND(MAX(CASE WHEN OverTime = 'Yes' THEN rate END)
           / MAX(CASE WHEN OverTime = 'No' THEN rate END), 1)        AS overtime_multiple
FROM ot;

-- 3.2 Highest-risk segment: job level x overtime
SELECT JobLevel,
       OverTime,
       COUNT(*)                                                   AS employees,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)         AS leavers,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees
GROUP BY JobLevel, OverTime
ORDER BY attrition_rate_pct DESC;

-- 3.3 Satisfaction and work-life balance (1 = lowest, 4 = highest)
SELECT 'Job satisfaction' AS factor, JobSatisfaction AS score,
       COUNT(*) AS employees,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees GROUP BY JobSatisfaction
UNION ALL
SELECT 'Work-life balance', WorkLifeBalance, COUNT(*),
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1)
FROM hr_employees GROUP BY WorkLifeBalance
UNION ALL
SELECT 'Environment satisfaction', EnvironmentSatisfaction, COUNT(*),
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1)
FROM hr_employees GROUP BY EnvironmentSatisfaction
ORDER BY factor, score;

-- 3.4 Business travel, marital status and stock options
SELECT 'Business travel' AS factor, BusinessTravel AS value_, COUNT(*) AS employees,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees GROUP BY BusinessTravel
UNION ALL
SELECT 'Marital status', MaritalStatus, COUNT(*),
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1)
FROM hr_employees GROUP BY MaritalStatus
UNION ALL
SELECT 'Stock option level', CAST(StockOptionLevel AS CHAR), COUNT(*),
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1)
FROM hr_employees GROUP BY StockOptionLevel
ORDER BY factor, attrition_rate_pct DESC;

-- ============================================================
-- 4. Compensation
-- ============================================================

-- 4.1 Pay range per job level (overlap between levels = pay compression)
SELECT JobLevel,
       COUNT(*)                     AS employees,
       MIN(MonthlyIncome)           AS min_income,
       ROUND(AVG(MonthlyIncome), 0) AS avg_income,
       MAX(MonthlyIncome)           AS max_income
FROM hr_employees
GROUP BY JobLevel
ORDER BY JobLevel;

-- 4.2 Attrition by income band
SELECT CASE WHEN MonthlyIncome < 3000  THEN '1) Under 3K'
            WHEN MonthlyIncome < 5000  THEN '2) 3K-5K'
            WHEN MonthlyIncome < 10000 THEN '3) 5K-10K'
            ELSE '4) 10K+' END                                    AS income_band,
       COUNT(*)                                                   AS employees,
       SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)         AS leavers,
       ROUND(100.0 * AVG(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END), 1) AS attrition_rate_pct
FROM hr_employees
GROUP BY 1
ORDER BY 1;

-- 4.3 Gender pay gap by job role (positive gap = men paid more on average)
SELECT JobRole,
       ROUND(AVG(CASE WHEN Gender = 'Male'   THEN MonthlyIncome END), 0) AS avg_male,
       ROUND(AVG(CASE WHEN Gender = 'Female' THEN MonthlyIncome END), 0) AS avg_female,
       ROUND(100.0 * (AVG(CASE WHEN Gender = 'Male' THEN MonthlyIncome END)
                    - AVG(CASE WHEN Gender = 'Female' THEN MonthlyIncome END))
                    / AVG(CASE WHEN Gender = 'Male' THEN MonthlyIncome END), 1) AS gap_pct
FROM hr_employees
GROUP BY JobRole
ORDER BY gap_pct DESC;

-- 4.4 Employees paid below their job level's median (candidates for a pay review)
WITH ranked AS (
    SELECT EmployeeNumber, JobLevel, JobRole, MonthlyIncome, Attrition,
           ROW_NUMBER() OVER (PARTITION BY JobLevel ORDER BY MonthlyIncome) AS rn,
           COUNT(*)     OVER (PARTITION BY JobLevel)                        AS n
    FROM hr_employees
),
level_median AS (
    SELECT JobLevel, AVG(MonthlyIncome) AS median_income
    FROM ranked
    WHERE rn BETWEEN n / 2.0 AND n / 2.0 + 1   -- the middle row (odd n) or two middle rows (even n)
    GROUP BY JobLevel
)
SELECT r.JobLevel,
       ROUND(m.median_income, 0)                                  AS level_median,
       SUM(CASE WHEN r.MonthlyIncome < m.median_income THEN 1 ELSE 0 END) AS below_median,
       ROUND(100.0 * AVG(CASE WHEN r.MonthlyIncome <  m.median_income AND r.Attrition = 'Yes' THEN 1.0
                              WHEN r.MonthlyIncome <  m.median_income THEN 0 END), 1) AS below_median_attrition_pct,
       ROUND(100.0 * AVG(CASE WHEN r.MonthlyIncome >= m.median_income AND r.Attrition = 'Yes' THEN 1.0
                              WHEN r.MonthlyIncome >= m.median_income THEN 0 END), 1) AS at_or_above_median_attrition_pct
FROM ranked r
JOIN level_median m ON m.JobLevel = r.JobLevel
GROUP BY r.JobLevel, m.median_income
ORDER BY r.JobLevel;

-- ============================================================
-- 5. What-if: cost of attrition vs cost of a raise
--    Assumption: replacing a leaver costs 50% of their annual salary
--    (hiring, onboarding, lost output). The dashboard makes this a slider.
-- ============================================================

-- 5.1 Estimated attrition cost and a 10% raise for Job Level 1 stayers
WITH lvl1 AS (
    SELECT SUM(CASE WHEN Attrition = 'Yes' THEN MonthlyIncome * 12 * 0.50 ELSE 0 END) AS attrition_cost,
           SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)                         AS leavers,
           SUM(CASE WHEN Attrition = 'No'  THEN MonthlyIncome * 12 * 0.10 ELSE 0 END) AS raise_cost
    FROM hr_employees
    WHERE JobLevel = 1
)
SELECT ROUND(attrition_cost, 0)                       AS level1_attrition_cost,
       leavers                                        AS level1_leavers,
       ROUND(attrition_cost / leavers, 0)             AS cost_per_leaver,
       ROUND(raise_cost, 0)                           AS level1_raise_cost_10pct,
       ROUND(raise_cost / (attrition_cost / leavers), 0) AS leavers_to_prevent_to_break_even
FROM lvl1;
