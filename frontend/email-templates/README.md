# Email Templates

Branded HTML email templates for CodePulse. These are pasted manually into the Supabase dashboard.
Supabase does not read them from this folder automatically.

---

## How to apply a template

1. Go to [Supabase Dashboard](https://supabase.com/dashboard) → select your project
2. Navigate to **Authentication** → **Email Templates**
3. Select the template you want to update from the left list
4. Replace the entire body with the contents of the corresponding file below
5. Click **Save**

---

## Template files

| File | Supabase template name |
|------|----------------------|
| `confirm-signup.html` | Confirm signup |
| `reset-password.html` | Reset password |
| `invite-user.html` | Invite user |

---

## Notes

- The `{{ .ConfirmationURL }}` placeholder is replaced automatically by Supabase when emails are sent — do not change it.
- Templates use inline styles for maximum email client compatibility.
- To change the sender name, go to **Authentication** → **Email Settings** → set **From name** to `CodePulse`.
- The invite template requires `https://code-pulse-six.vercel.app` to be in **Authentication** → **URL Configuration** → **Redirect URLs**.
