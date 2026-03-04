-- 0. Clean up existing tables (Run this first)
DROP TABLE IF EXISTS actionable_fixes CASCADE;
DROP TABLE IF EXISTS findings CASCADE;
DROP TABLE IF EXISTS analysis_reports CASCADE;
DROP TABLE IF EXISTS submissions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. Regular Entity: User
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, 
    role TEXT DEFAULT 'developer',
    profile_picture TEXT,
    creation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Regular Entity: Submission
CREATE TABLE submissions (
    submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Regular Entity: AnalysisReport
CREATE TABLE analysis_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID UNIQUE REFERENCES submissions(submission_id) ON DELETE CASCADE,
    overall_score INT CHECK (overall_score >= 0 AND overall_score <= 100),
    summary TEXT
);

-- 4. Weak Entity: Finding
CREATE TABLE findings (
    finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES analysis_reports(report_id) ON DELETE CASCADE,
    issue_type TEXT NOT NULL,
    line_number INT NOT NULL,
    line_severity TEXT NOT NULL CHECK (line_severity IN ('Low', 'Med', 'High')),
    message TEXT NOT NULL
);

-- 5. Associative Entity: ActionableFix
CREATE TABLE actionable_fixes (
    fix_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID UNIQUE REFERENCES findings(finding_id) ON DELETE CASCADE,
    original_snippet TEXT NOT NULL,
    suggested_snippet TEXT NOT NULL,
    rationale TEXT,
    tags TEXT[] 
);