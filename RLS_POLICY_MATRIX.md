# TalentLens: Comprehensive PostgreSQL Row-Level Security (RLS) Policy Matrix

**Document Version**: 4.0  
**Status**: Authoritative Security Specification  
**Database Engine**: PostgreSQL 16  
**Application Database Role**: `talentlens_app` (`NOBYPASSRLS`, non-superuser)  
**Security Definer Owner**: `talentlens_admin` (schema owner / migration role)  

---

## 1. Global RLS Architecture & Operating Principles

1. **Permissive Base Policies**: All primary access rules are declared `AS PERMISSIVE` (the default in PostgreSQL). In PostgreSQL, multiple `PERMISSIVE` policies are combined with boolean `OR`. Restrictive policies (`AS RESTRICTIVE`) are used only when an unconditional filter must be combined with boolean `AND` across all permissive checks.
2. **Dual Context Enforcement**: Every tenant-scoped operation verifies both `app.current_user_id` and `app.current_org_id` using the security-definer helper function `fn_has_active_org_membership(org_id, required_role)`.
3. **Defense-in-Depth Separation**:
   - Database Role `talentlens_app` has minimal required DML rights (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on `public` tables.
   - `FORCE ROW LEVEL SECURITY` is enabled on all sensitive tables to ensure policies apply even if queries execute under table owners.
   - API middleware independently validates JWT signatures, active organization memberships, and role permissions before queries are dispatched.
4. **Clean Transaction Scope**: Session variables are injected exclusively via parameterized `set_config(name, value, true)`, ensuring automatic cleanup when transactions commit or roll back.

---

## 2. Helper Functions (Security Definer with Search Path)

```sql
-- Helper 1: Validate active organization membership and role hierarchy
CREATE OR REPLACE FUNCTION public.fn_has_active_org_membership(
    p_org_id UUID,
    p_min_role public.organization_role DEFAULT 'VIEWER'
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_user_id UUID;
    v_active_org_id UUID;
    v_actual_role public.organization_role;
    v_role_level INT;
    v_req_level INT;
BEGIN
    v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::UUID;
    v_active_org_id := NULLIF(current_setting('app.current_org_id', true), '')::UUID;

    -- Both contexts must be initialized and match the target organization
    IF v_user_id IS NULL OR v_active_org_id IS NULL OR v_active_org_id <> p_org_id THEN
        RETURN FALSE;
    END IF;

    SELECT role INTO v_actual_role
    FROM public.organization_memberships
    WHERE organization_id = p_org_id
      AND user_id = v_user_id
      AND is_active = TRUE;

    IF v_actual_role IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Map roles to numeric hierarchy: OWNER(40) >= ADMIN(30) >= RECRUITER(20) >= VIEWER(10)
    v_role_level := CASE v_actual_role
        WHEN 'OWNER' THEN 40
        WHEN 'ADMIN' THEN 30
        WHEN 'RECRUITER' THEN 20
        WHEN 'VIEWER' THEN 10
        ELSE 0
    END;

    v_req_level := CASE p_min_role
        WHEN 'OWNER' THEN 40
        WHEN 'ADMIN' THEN 30
        WHEN 'RECRUITER' THEN 20
        WHEN 'VIEWER' THEN 10
        ELSE 0
    END;

    RETURN v_role_level >= v_req_level;
END;
$$;

-- Helper 2: Verify candidate ownership
CREATE OR REPLACE FUNCTION public.fn_is_candidate_owner(p_candidate_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT p_candidate_id IS NOT NULL 
       AND p_candidate_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID;
$$;
```

---

## 3. Comprehensive Table-by-Table Policy Matrix

| Table Name | RLS / FORCE | Operation | Policy Name | Active Org & Role Required | Ownership Model | `USING` Predicate | `WITH CHECK` Predicate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`organizations`** | YES / YES | `SELECT` | `org_select_policy` | Active member (`VIEWER`+) OR public active metadata | Tenant-Scoped / Public | `fn_has_active_org_membership(id, 'VIEWER') OR is_active = TRUE` | N/A |
| `organizations` | YES / YES | `INSERT` | `org_insert_policy` | Authenticated Platform User | User-Initiated | `NULLIF(current_setting('app.current_user_id', true), '') IS NOT NULL` | `NULLIF(current_setting('app.current_user_id', true), '') IS NOT NULL` |
| `organizations` | YES / YES | `UPDATE` | `org_update_policy` | `OWNER` or `ADMIN` | Tenant Admin | `fn_has_active_org_membership(id, 'ADMIN')` | `fn_has_active_org_membership(id, 'ADMIN')` |
| `organizations` | YES / YES | `DELETE` | `org_delete_policy` | `OWNER` only | Tenant Owner | `fn_has_active_org_membership(id, 'OWNER')` | N/A |
| **`organization_memberships`** | YES / YES | `SELECT` | `org_mem_select` | User is self OR active member (`VIEWER`+) | Multi-Party | `user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID OR fn_has_active_org_membership(organization_id, 'VIEWER')` | N/A |
| `organization_memberships` | YES / YES | `INSERT` | `org_mem_insert` | `OWNER` or `ADMIN` (or system bootstrap) | Tenant Admin | N/A | `fn_has_active_org_membership(organization_id, 'ADMIN')` |
| `organization_memberships` | YES / YES | `UPDATE` | `org_mem_update` | `OWNER` or `ADMIN` | Tenant Admin | `fn_has_active_org_membership(organization_id, 'ADMIN')` | `fn_has_active_org_membership(organization_id, 'ADMIN')` |
| `organization_memberships` | YES / YES | `DELETE` | `org_mem_delete` | `OWNER` or `ADMIN` (cannot delete last owner) | Tenant Admin | `fn_has_active_org_membership(organization_id, 'ADMIN')` | N/A |
| **`users`** | YES / YES | `SELECT` | `users_select` | Self OR verified co-member / applicant review | Dual-Sided | `id = NULLIF(current_setting('app.current_user_id', true), '')::UUID OR EXISTS (SELECT 1 FROM organization_memberships om WHERE om.user_id = users.id AND fn_has_active_org_membership(om.organization_id, 'VIEWER')) OR EXISTS (SELECT 1 FROM job_applications ja JOIN jobs j ON j.id = ja.job_id WHERE ja.candidate_id = users.id AND fn_has_active_org_membership(j.organization_id, 'RECRUITER'))` | N/A |
| `users` | YES / YES | `INSERT` | `users_insert` | Public Registration / Self | Self | `TRUE` | `TRUE` |
| `users` | YES / YES | `UPDATE` | `users_update` | Self only | Self | `id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` | `id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` |
| `users` | YES / YES | `DELETE` | `users_delete` | Self only | Self | `id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` | N/A |
| **`candidate_profiles`** | YES / YES | `SELECT` | `cand_prof_select` | Owning Candidate OR authorized Recruiter | Candidate-Owned | `fn_is_candidate_owner(user_id) OR EXISTS (SELECT 1 FROM job_applications ja JOIN jobs j ON j.id = ja.job_id WHERE ja.candidate_id = candidate_profiles.user_id AND fn_has_active_org_membership(j.organization_id, 'RECRUITER'))` | N/A |
| `candidate_profiles` | YES / YES | `INSERT/UPDATE`| `cand_prof_mod` | Owning Candidate only | Candidate-Owned | `fn_is_candidate_owner(user_id)` | `fn_is_candidate_owner(user_id)` |
| `candidate_profiles` | YES / YES | `DELETE` | `cand_prof_del` | Owning Candidate only | Candidate-Owned | `fn_is_candidate_owner(user_id)` | N/A |
| **`resumes`** | YES / YES | `SELECT` | `resumes_select` | Owning Candidate OR Recruiter via submitted application | Candidate-Owned | `fn_is_candidate_owner(candidate_id) OR id IN (SELECT ja.submitted_resume_id FROM job_applications ja JOIN jobs j ON j.id = ja.job_id WHERE fn_has_active_org_membership(j.organization_id, 'RECRUITER'))` | N/A |
| `resumes` | YES / YES | `INSERT` | `resumes_insert` | Owning Candidate only | Candidate-Owned | N/A | `fn_is_candidate_owner(candidate_id)` |
| `resumes` | YES / YES | `UPDATE` | `resumes_update` | Owning Candidate only (Unsubmitted only) | Candidate-Owned | `fn_is_candidate_owner(candidate_id)` | `fn_is_candidate_owner(candidate_id)` |
| `resumes` | YES / YES | `DELETE` | `resumes_delete` | Owning Candidate only (Unsubmitted only) | Candidate-Owned | `fn_is_candidate_owner(candidate_id)` | N/A |
| **`resume_sections`** | YES / YES | `SELECT` | `sec_select` | Inherited from `resumes` | Candidate-Owned | `EXISTS (SELECT 1 FROM resumes r WHERE r.id = resume_sections.resume_id AND (fn_is_candidate_owner(r.candidate_id) OR r.id IN (SELECT ja.submitted_resume_id FROM job_applications ja JOIN jobs j ON j.id = ja.job_id WHERE fn_has_active_org_membership(j.organization_id, 'RECRUITER'))))` | N/A |
| `resume_sections` | YES / YES | `INSERT/UPDATE/DELETE`| `sec_modify` | Owning Candidate only | Candidate-Owned | `EXISTS (SELECT 1 FROM resumes r WHERE r.id = resume_sections.resume_id AND fn_is_candidate_owner(r.candidate_id))` | `EXISTS (SELECT 1 FROM resumes r WHERE r.id = resume_sections.resume_id AND fn_is_candidate_owner(r.candidate_id))` |
| **`resume_skills`** | YES / YES | `SELECT` | `skills_select` | Inherited from `resumes` | Candidate-Owned | `EXISTS (SELECT 1 FROM resumes r WHERE r.id = resume_skills.resume_id AND (fn_is_candidate_owner(r.candidate_id) OR r.id IN (SELECT ja.submitted_resume_id FROM job_applications ja JOIN jobs j ON j.id = ja.job_id WHERE fn_has_active_org_membership(j.organization_id, 'RECRUITER'))))` | N/A |
| `resume_skills` | YES / YES | `INSERT/UPDATE/DELETE`| `skills_modify` | Owning Candidate only | Candidate-Owned | `EXISTS (SELECT 1 FROM resumes r WHERE r.id = resume_skills.resume_id AND fn_is_candidate_owner(r.candidate_id))` | `EXISTS (SELECT 1 FROM resumes r WHERE r.id = resume_skills.resume_id AND fn_is_candidate_owner(r.candidate_id))` |
| **`jobs`** | YES / YES | `SELECT` | `jobs_select` | Active member (`VIEWER`+) OR public `PUBLISHED` | Tenant-Scoped / Public | `fn_has_active_org_membership(organization_id, 'VIEWER') OR status = 'PUBLISHED'` | N/A |
| `jobs` | YES / YES | `INSERT` | `jobs_insert` | `RECRUITER`+ in active organization | Tenant-Scoped | N/A | `fn_has_active_org_membership(organization_id, 'RECRUITER')` |
| `jobs` | YES / YES | `UPDATE` | `jobs_update` | `RECRUITER`+ in active organization | Tenant-Scoped | `fn_has_active_org_membership(organization_id, 'RECRUITER')` | `fn_has_active_org_membership(organization_id, 'RECRUITER')` |
| `jobs` | YES / YES | `DELETE` | `jobs_delete` | `ADMIN`+ in active organization | Tenant Admin | `fn_has_active_org_membership(organization_id, 'ADMIN')` | N/A |
| **`job_applications`** | YES / YES | `SELECT` | `app_select` | Submitting Candidate OR active `RECRUITER`+ | Application Junction | `fn_is_candidate_owner(candidate_id) OR EXISTS (SELECT 1 FROM jobs j WHERE j.id = job_applications.job_id AND fn_has_active_org_membership(j.organization_id, 'RECRUITER'))` | N/A |
| `job_applications` | YES / YES | `INSERT` | `app_insert` | Submitting Candidate only | Candidate-Owned | N/A | `fn_is_candidate_owner(candidate_id)` |
| `job_applications` | YES / YES | `UPDATE` | `app_update` | Active `RECRUITER`+ (Status fields only) | Recruiter Status Action | `EXISTS (SELECT 1 FROM jobs j WHERE j.id = job_applications.job_id AND fn_has_active_org_membership(j.organization_id, 'RECRUITER'))` | `EXISTS (SELECT 1 FROM jobs j WHERE j.id = job_applications.job_id AND fn_has_active_org_membership(j.organization_id, 'RECRUITER'))` |
| `job_applications` | YES / YES | `DELETE` | `app_delete` | Disallowed for all application roles | Protected History | `FALSE` | N/A |
| **`screening_runs`** | YES / YES | `SELECT` | `runs_select` | Active member (`VIEWER`+) | Tenant-Scoped | `fn_has_active_org_membership(organization_id, 'VIEWER')` | N/A |
| `screening_runs` | YES / YES | `INSERT` | `runs_insert` | Active `RECRUITER`+ | Tenant-Scoped | N/A | `fn_has_active_org_membership(organization_id, 'RECRUITER')` |
| `screening_runs` | YES / YES | `UPDATE` | `runs_update` | Active `RECRUITER`+ (while uncompleted) | Tenant-Scoped | `fn_has_active_org_membership(organization_id, 'RECRUITER')` | `fn_has_active_org_membership(organization_id, 'RECRUITER')` |
| `screening_runs` | YES / YES | `DELETE` | `runs_delete` | Active `ADMIN`+ (while uncompleted) | Tenant Admin | `fn_has_active_org_membership(organization_id, 'ADMIN')` | N/A |
| **`screening_results`** | YES / YES | `SELECT` | `results_select` | Active member (`VIEWER`+) | Tenant-Scoped | `EXISTS (SELECT 1 FROM screening_runs sr WHERE sr.id = screening_results.screening_run_id AND fn_has_active_org_membership(sr.organization_id, 'VIEWER'))` | N/A |
| `screening_results` | YES / YES | `INSERT` | `results_insert` | System / Async Screening Worker | Internal Pipeline | N/A | `EXISTS (SELECT 1 FROM screening_runs sr WHERE sr.id = screening_results.screening_run_id AND fn_has_active_org_membership(sr.organization_id, 'RECRUITER'))` |
| `screening_results` | YES / YES | `UPDATE/DELETE`| `results_immutable` | Disallowed once completed (Trigger enforced) | Immutable Snapshot | `FALSE` | N/A |
| **`candidate_rag_sessions`**| YES / YES| `ALL` | `cand_rag_all` | Owning Candidate only | Candidate-Owned | `fn_is_candidate_owner(candidate_id)` | `fn_is_candidate_owner(candidate_id)` |
| **`recruiter_rag_sessions`**| YES / YES| `ALL` | `rec_rag_all` | Active `RECRUITER`+ in matching org | Tenant Recruiter | `fn_has_active_org_membership(organization_id, 'RECRUITER') AND recruiter_user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` | `fn_has_active_org_membership(organization_id, 'RECRUITER') AND recruiter_user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` |
| **`rag_chat_messages`** | YES / YES | `SELECT` | `chat_select` | Owner of parent candidate or recruiter session | Multi-Party Session | `(candidate_session_id IS NOT NULL AND EXISTS (SELECT 1 FROM candidate_rag_sessions cs WHERE cs.id = candidate_session_id AND fn_is_candidate_owner(cs.candidate_id))) OR (recruiter_session_id IS NOT NULL AND EXISTS (SELECT 1 FROM recruiter_rag_sessions rs WHERE rs.id = recruiter_session_id AND fn_has_active_org_membership(rs.organization_id, 'RECRUITER') AND rs.recruiter_user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID))` | N/A |
| `rag_chat_messages` | YES / YES | `INSERT` | `chat_insert` | Owner of parent session (USER role enforced) | Session Participant | N/A | `((candidate_session_id IS NOT NULL AND EXISTS (SELECT 1 FROM candidate_rag_sessions cs WHERE cs.id = candidate_session_id AND fn_is_candidate_owner(cs.candidate_id))) OR (recruiter_session_id IS NOT NULL AND EXISTS (SELECT 1 FROM recruiter_rag_sessions rs WHERE rs.id = recruiter_session_id AND fn_has_active_org_membership(rs.organization_id, 'RECRUITER') AND rs.recruiter_user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID))) AND sender_role = 'USER'` |
| `rag_chat_messages` | YES / YES | `UPDATE/DELETE`| `chat_modify` | Disallowed (Append-only conversation) | Immutable Messages | `FALSE` | N/A |
| **`audit_logs`** | YES / YES | `SELECT` | `audit_select` | Acting candidate user OR active `ADMIN`+ in org | Compliance Audit | `(user_id IS NOT NULL AND fn_is_candidate_owner(user_id)) OR (organization_id IS NOT NULL AND fn_has_active_org_membership(organization_id, 'ADMIN'))` | N/A |
| `audit_logs` | YES / YES | `INSERT` | `audit_insert` | System append-only (Function enforced) | System Audit | N/A | `TRUE` |
| `audit_logs` | YES / YES | `UPDATE/DELETE`| `audit_immutable`| Disallowed completely | Tamper-Proof Audit | `FALSE` | N/A |
| **`idempotency_keys`** | YES / YES | `SELECT/INSERT/UPDATE`| `idempotency_owner` | Owning user only | Idempotency State | `user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` | `user_id = NULLIF(current_setting('app.current_user_id', true), '')::UUID` |
| `idempotency_keys` | YES / YES | `DELETE` | `idempotency_del` | Disallowed for ordinary users | System Purge | `FALSE` | N/A |

---

## 4. Operational RBAC Permission Matrix

| Capability / Action | Minimum Organization Role Required | Enforced By |
| :--- | :--- | :--- |
| **Create Organization** | Any Authenticated Platform User | API + `organizations` INSERT policy |
| **Delete / Deactivate Organization** | `OWNER` | API + `organizations` DELETE policy |
| **Transfer Organization Ownership** | `OWNER` | Dedicated Service Function (`fn_transfer_org_ownership`) |
| **Invite Member / Change Roles** | `ADMIN` (cannot assign or modify `OWNER`) | API + `organization_memberships` UPDATE policy |
| **Revoke Member** | `ADMIN` (cannot revoke `OWNER`) | API + `organization_memberships` DELETE policy |
| **Create / Edit / Publish Requisitions**| `RECRUITER` | API + `jobs` INSERT/UPDATE policy |
| **Close / Archive Requisitions** | `RECRUITER` | API + `jobs` UPDATE policy |
| **Delete Draft Requisitions** | `ADMIN` | API + `jobs` DELETE policy (`RESTRICT` on apps) |
| **View Submitted Candidate Resumes** | `RECRUITER` | API + `resumes` / `job_applications` SELECT |
| **Trigger Asynchronous Screening Run**| `RECRUITER` | API + `screening_runs` INSERT policy |
| **View Screening Results & Evidence** | `VIEWER` | API + `screening_results` SELECT policy |
| **Change Application Review Status** | `RECRUITER` | API + `job_applications` UPDATE trigger |
| **Engage Requisition Copilot RAG** | `RECRUITER` | API + `recruiter_rag_sessions` ALL policy |
| **View Organization Audit Logs** | `ADMIN` | API + `audit_logs` SELECT policy |
