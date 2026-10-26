-- ============================================================================
-- 01_clean.sql
-- Input : raw_appointments  (the Kaggle CSV loaded as-is by run_analysis.py)
-- Output: appointments      (clean table, one row per appointment)
--
-- Cleaning decisions (all counts are printed by run_analysis.py):
--   * Column typos fixed: Hipertension -> hypertension, Handcap -> handicap_level
--   * "No-show" text (Yes/No) -> no_show 0/1   (1 = patient did NOT show up)
--   * Drop Age < 0                 (impossible value)
--   * Drop appointment_date < scheduled_date (appointment before booking: impossible)
--   * Keep Age = 0 (genuine infants) and Age 100+ (rare, but not provably wrong)
--   * Handcap is 0-4 in the data, not a yes/no flag as the Kaggle description
--     implies, so we keep the raw level AND add a handicap = 0/1 flag
--   * AppointmentDay has no time-of-day in the source, so lead time is measured
--     in whole days (appointment_date - scheduled_date)
-- ============================================================================

DROP TABLE IF EXISTS appointments;

CREATE TABLE appointments AS
WITH base AS (
    SELECT
        CAST(PatientId AS INTEGER)                                   AS patient_id,
        AppointmentID                                                AS appointment_id,
        Gender                                                       AS gender,
        date(ScheduledDay)                                           AS scheduled_date,
        date(AppointmentDay)                                         AS appointment_date,
        CAST(julianday(date(AppointmentDay))
           - julianday(date(ScheduledDay)) AS INTEGER)               AS lead_days,
        Age                                                          AS age,
        Neighbourhood                                                AS neighbourhood,
        Scholarship                                                  AS scholarship,
        Hipertension                                                 AS hypertension,
        Diabetes                                                     AS diabetes,
        Alcoholism                                                   AS alcoholism,
        Handcap                                                      AS handicap_level,
        CASE WHEN Handcap > 0 THEN 1 ELSE 0 END                      AS handicap,
        SMS_received                                                 AS sms_received,
        CASE "No-show" WHEN 'Yes' THEN 1 ELSE 0 END                  AS no_show
    FROM raw_appointments
    WHERE Age >= 0
      AND julianday(date(AppointmentDay)) >= julianday(date(ScheduledDay))
)
SELECT
    base.*,

    -- Buckets used throughout the analysis
    CASE
        WHEN lead_days = 0  THEN '1. Same day'
        WHEN lead_days <= 3 THEN '2. 1-3 days'
        WHEN lead_days <= 7 THEN '3. 4-7 days'
        WHEN lead_days <= 14 THEN '4. 8-14 days'
        WHEN lead_days <= 30 THEN '5. 15-30 days'
        ELSE                     '6. 31+ days'
    END AS lead_bucket,

    CASE
        WHEN age <= 12 THEN '1. 0-12'
        WHEN age <= 17 THEN '2. 13-17'
        WHEN age <= 29 THEN '3. 18-29'
        WHEN age <= 44 THEN '4. 30-44'
        WHEN age <= 59 THEN '5. 45-59'
        WHEN age <= 74 THEN '6. 60-74'
        ELSE                '7. 75+'
    END AS age_group,

    CAST(strftime('%w', appointment_date) AS INTEGER)                AS weekday_num,   -- 0 = Sunday
    CASE strftime('%w', appointment_date)
        WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue'
        WHEN '3' THEN 'Wed' WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri'
        ELSE 'Sat'
    END AS weekday,

    -- Patient history, using ONLY appointments on earlier days (no leakage).
    -- RANGE ... 1 PRECEDING over a day number excludes same-day appointments.
    -- Caveat: the data covers only ~6 weeks of appointments, so history is truncated.
    COUNT(*) OVER (
        PARTITION BY patient_id
        ORDER BY julianday(appointment_date)
        RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS prior_appointments,
    COALESCE(SUM(no_show) OVER (
        PARTITION BY patient_id
        ORDER BY julianday(appointment_date)
        RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ), 0) AS prior_no_shows
FROM base;

CREATE INDEX idx_appt_patient ON appointments (patient_id);
