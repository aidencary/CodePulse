-- ============================================================
-- CodePulse Supabase Schema Migration
-- Run in: Supabase Dashboard → SQL Editor → New query
-- ============================================================

-- 0. Clean up existing tables
DROP TABLE IF EXISTS actionable_fixes CASCADE;
DROP TABLE IF EXISTS findings CASCADE;
DROP TABLE IF EXISTS analysis_reports CASCADE;
DROP TABLE IF EXISTS submissions CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;

-- 1. Profiles table (1:1 with auth.users, auto-created on signup via trigger)
--    auth.users is managed by Supabase Auth — do NOT create it manually.
CREATE TABLE profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username        TEXT UNIQUE NOT NULL,
    role            TEXT DEFAULT 'developer',
    profile_picture TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Submissions (user_id references auth.users directly)
CREATE TABLE submissions (
    submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    code          TEXT NOT NULL,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Analysis Reports
CREATE TABLE analysis_reports (
    report_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID UNIQUE REFERENCES submissions(submission_id) ON DELETE CASCADE,
    overall_score INT CHECK (overall_score >= 0 AND overall_score <= 100),
    summary       TEXT
);

-- 4. Findings (Weak Entity)
CREATE TABLE findings (
    finding_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id     UUID REFERENCES analysis_reports(report_id) ON DELETE CASCADE,
    issue_type    TEXT NOT NULL,
    line_number   INT NOT NULL,
    line_severity TEXT NOT NULL CHECK (line_severity IN ('Low', 'Med', 'High')),
    message       TEXT NOT NULL
);

-- 5. Actionable Fixes (Associative Entity)
CREATE TABLE actionable_fixes (
    fix_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id       UUID UNIQUE REFERENCES findings(finding_id) ON DELETE CASCADE,
    original_snippet TEXT NOT NULL,
    suggested_snippet TEXT NOT NULL,
    rationale        TEXT,
    tags             TEXT[]
);

-- ============================================================
-- Row Level Security
-- ============================================================

ALTER TABLE profiles   ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;

-- Profiles: each user can only read/write their own row
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

-- Submissions: each user can only read/write their own rows
CREATE POLICY "Users can view own submissions"
    ON submissions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own submissions"
    ON submissions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Delete policies for profiles and submissions
CREATE POLICY "Users can delete own profile"
    ON profiles FOR DELETE
    USING (auth.uid() = id);

CREATE POLICY "Users can delete own submissions"
    ON submissions FOR DELETE
    USING (auth.uid() = user_id);

-- Analysis reports: visible only if the linked submission belongs to the user
ALTER TABLE analysis_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own analysis reports"
    ON analysis_reports FOR SELECT
    USING (
        submission_id IN (
            SELECT submission_id FROM submissions WHERE user_id = auth.uid()
        )
    );

-- Findings: visible only if the linked report belongs to the user
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own findings"
    ON findings FOR SELECT
    USING (
        report_id IN (
            SELECT report_id FROM analysis_reports
            WHERE submission_id IN (
                SELECT submission_id FROM submissions WHERE user_id = auth.uid()
            )
        )
    );

-- Actionable fixes: visible only if the linked finding belongs to the user
ALTER TABLE actionable_fixes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own actionable fixes"
    ON actionable_fixes FOR SELECT
    USING (
        finding_id IN (
            SELECT finding_id FROM findings
            WHERE report_id IN (
                SELECT report_id FROM analysis_reports
                WHERE submission_id IN (
                    SELECT submission_id FROM submissions WHERE user_id = auth.uid()
                )
            )
        )
    );

-- ============================================================
-- Auto-create profile row on signup
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, username)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
