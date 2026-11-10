import os
import sys
import json
import sqlite3
import shutil

def get_db_path():
    appdata = os.environ.get('APPDATA')
    if not appdata:
        appdata = os.path.expanduser(r'~\AppData\Roaming')
    return os.path.join(appdata, 'Antigravity IDE', 'User', 'globalStorage', 'state.vscdb')

def get_vault_dir(gemini_dir=None):
    if not gemini_dir:
        gemini_dir = os.path.expanduser(r'~/.gemini')
    vault = os.path.join(gemini_dir, 'accounts_vault')
    os.makedirs(vault, exist_ok=True)
    return vault

def get_active_account(gemini_dir=None):
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return {"error": "state.vscdb not found"}
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Read google.google-antigravity
    row_user = c.execute("SELECT value FROM ItemTable WHERE key='google.google-antigravity'").fetchone()
    email = "Unknown"
    if row_user and row_user[0]:
        try:
            data = json.loads(row_user[0])
            storage = data.get("antigravity-storage", {})
            email = storage.get("agy.onboarding.lastLoginUsername", "Unknown")
        except Exception:
            pass

    row_token = c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.oauthToken'").fetchone()
    oauth_token = row_token[0] if row_token else None

    row_status = c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.userStatus'").fetchone()
    user_status = row_status[0] if row_status else None
    conn.close()

    pbtxt_path = os.path.join(gemini_dir or os.path.expanduser(r'~/.gemini'), 'antigravity', 'antigravity_state.pbtxt')
    has_pbtxt = os.path.exists(pbtxt_path)

    return {
        "email": email,
        "hasToken": bool(oauth_token),
        "tokenLength": len(oauth_token) if oauth_token else 0,
        "hasStatus": bool(user_status),
        "hasPbtxt": has_pbtxt
    }

def list_vault_accounts(gemini_dir=None):
    vault = get_vault_dir(gemini_dir)
    active = get_active_account(gemini_dir)
    active_email = active.get("email", "")

    accounts = []
    for item in os.listdir(vault):
        item_path = os.path.join(vault, item)
        if os.path.isdir(item_path):
            meta_path = os.path.join(item_path, "account.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["isActive"] = (meta.get("email", "").lower() == active_email.lower())
                    accounts.append(meta)
                except Exception:
                    pass

    return {
        "activeAccount": active,
        "vaultAccounts": accounts
    }

def save_current_account(gemini_dir=None, label=None):
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return {"success": False, "error": "state.vscdb not found"}

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    row_user = c.execute("SELECT value FROM ItemTable WHERE key='google.google-antigravity'").fetchone()
    email = "Unknown"
    storage_blob = "{}"
    if row_user and row_user[0]:
        storage_blob = row_user[0]
        try:
            data = json.loads(storage_blob)
            storage = data.get("antigravity-storage", {})
            email = storage.get("agy.onboarding.lastLoginUsername", "Unknown")
        except Exception:
            pass

    if not email or email == "Unknown":
        conn.close()
        return {"success": False, "error": "No logged-in account email found in state.vscdb"}

    row_token = c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.oauthToken'").fetchone()
    oauth_token = row_token[0] if row_token else ""

    row_status = c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.userStatus'").fetchone()
    user_status = row_status[0] if row_status else ""
    conn.close()

    vault = get_vault_dir(gemini_dir)
    safe_folder = email.replace("@", "_at_").replace(".", "_")
    acc_dir = os.path.join(vault, safe_folder)
    os.makedirs(acc_dir, exist_ok=True)

    # Save tokens & blobs
    with open(os.path.join(acc_dir, "oauthToken.dat"), "w", encoding="utf-8") as f:
        f.write(oauth_token)

    with open(os.path.join(acc_dir, "userStatus.dat"), "w", encoding="utf-8") as f:
        f.write(user_status)

    with open(os.path.join(acc_dir, "googleAntigravity.json"), "w", encoding="utf-8") as f:
        f.write(storage_blob)

    # Copy pbtxt if exists
    active_gemini = gemini_dir or os.path.expanduser(r'~/.gemini')
    pbtxt_src = os.path.join(active_gemini, 'antigravity', 'antigravity_state.pbtxt')
    if os.path.exists(pbtxt_src):
        shutil.copy2(pbtxt_src, os.path.join(acc_dir, "antigravity_state.pbtxt"))

    # Meta
    meta = {
        "email": email,
        "folder": safe_folder,
        "label": label or email.split("@")[0],
        "savedAt": meta_get_time(),
        "lastSyncedAt": meta_get_time()
    }
    with open(os.path.join(acc_dir, "account.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {"success": True, "message": f"Account '{email}' saved into vault.", "account": meta}

def switch_account(target_email, gemini_dir=None):
    vault = get_vault_dir(gemini_dir)
    safe_folder = target_email.replace("@", "_at_").replace(".", "_")
    acc_dir = os.path.join(vault, safe_folder)

    if not os.path.exists(acc_dir):
        return {"success": False, "error": f"Account '{target_email}' not found in vault."}

    # Read saved data
    try:
        with open(os.path.join(acc_dir, "oauthToken.dat"), "r", encoding="utf-8") as f:
            oauth_token = f.read()
        with open(os.path.join(acc_dir, "userStatus.dat"), "r", encoding="utf-8") as f:
            user_status = f.read()
        with open(os.path.join(acc_dir, "googleAntigravity.json"), "r", encoding="utf-8") as f:
            storage_blob = f.read()
    except Exception as e:
        return {"success": False, "error": f"Failed reading vault account data: {str(e)}"}

    # Update state.vscdb
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return {"success": False, "error": "state.vscdb not found"}

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES ('antigravityUnifiedStateSync.oauthToken', ?)", (oauth_token,))
        c.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES ('antigravityUnifiedStateSync.userStatus', ?)", (user_status,))
        c.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES ('google.google-antigravity', ?)", (storage_blob,))
        conn.commit()
        conn.close()
    except Exception as e:
        return {"success": False, "error": f"Failed updating state.vscdb: {str(e)}"}

    # Copy pbtxt back
    active_gemini = gemini_dir or os.path.expanduser(r'~/.gemini')
    pbtxt_src = os.path.join(acc_dir, "antigravity_state.pbtxt")
    pbtxt_dst = os.path.join(active_gemini, 'antigravity', 'antigravity_state.pbtxt')
    if os.path.exists(pbtxt_src):
        os.makedirs(os.path.dirname(pbtxt_dst), exist_ok=True)
        shutil.copy2(pbtxt_src, pbtxt_dst)

    return {"success": True, "message": f"Successfully switched to '{target_email}'. Reload Antigravity window to apply."}

def delete_account(target_email, gemini_dir=None):
    vault = get_vault_dir(gemini_dir)
    safe_folder = target_email.replace("@", "_at_").replace(".", "_")
    acc_dir = os.path.join(vault, safe_folder)
    if os.path.exists(acc_dir):
        shutil.rmtree(acc_dir)
        return {"success": True, "message": f"Account '{target_email}' removed from vault."}
    return {"success": False, "error": "Account not found in vault."}

def meta_get_time():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    arg1 = sys.argv[2] if len(sys.argv) > 2 else None
    arg2 = sys.argv[3] if len(sys.argv) > 3 else None

    if cmd == 'list':
        print(json.dumps(list_vault_accounts(arg1)))
    elif cmd == 'save':
        print(json.dumps(save_current_account(arg1, arg2)))
    elif cmd == 'switch':
        print(json.dumps(switch_account(arg1, arg2)))
    elif cmd == 'delete':
        print(json.dumps(delete_account(arg1, arg2)))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
