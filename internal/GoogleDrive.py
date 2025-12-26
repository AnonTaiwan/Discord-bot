from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json
from pathlib import Path
from datetime import datetime
from googleapiclient.discovery import build, MediaFileUpload

current_dir = Path(__file__).parent

def get_detailed_token_info(client_id=None, client_secret=None, refresh_token=None):
    # 填入你的憑證資訊
    info = {
        "client_id": client_id or input("你的_CLIENT_ID: "),
        "client_secret": client_secret or input("你的_CLIENT_SECRET: "),
        "refresh_token": refresh_token or input("你的_REFRESH_TOKEN: "),
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    # 1. 建立 Credentials 物件
    creds = Credentials.from_authorized_user_info(info)

    # 2. 檢查並刷新
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print("正在刷新 Token...")
            creds.refresh(Request())
    
    # 3. 取得所有欄位資訊
    # 這些屬性會在 refresh() 執行後自動更新
    details = {
        "access_token": creds.token,
        # 使用 .isoformat() 將 datetime 轉為 "2023-10-27T10:00:00..." 的字串
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
        "scopes": creds.scopes,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }

    # with open(current_dir / "detailed_token_info.json", "w") as f:
    #     json.dump(details, f, indent=4)

    # print("--- 刷新後的詳細資訊 ---")
    # for key, value in details.items():
    #     print(f"{key}: {value}")
        
    return creds

def get_or_create_folder(folder_name, creds):
    service = build('drive', 'v3', credentials=creds)
    
    # 1. 搜尋是否有同名的資料夾
    # q 參數說明：
    # name = '...' 指定名稱
    # mimeType = 'application/vnd.google-apps.folder' 限制只搜尋資料夾
    # trashed = false 排除垃圾桶內的檔案
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    
    results = service.files().list(
        q=query, 
        fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])

    if items:
        # 如果找到了，回傳第一個找到的 ID
        folder_id = items[0]['id']
        print(f"找到現有資料夾：{folder_name} (ID: {folder_id})")
        return folder_id
    else:
        # 2. 如果找不到，則建立一個新資料夾
        print(f"找不到資料夾 '{folder_name}'，正在建立...")
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        new_folder = service.files().create(
            body=folder_metadata, 
            fields='id'
        ).execute()
        
        folder_id = new_folder.get('id')
        print(f"成功建立資料夾！(ID: {folder_id})")
        return folder_id

def check_folder_path(creds, folder_path):
    service = build('drive', 'v3', credentials=creds)
    folder_names = folder_path.strip('/').split('/')
    parent_id = 'root'  # 從根目錄開始

    for folder_name in folder_names:
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
        
        results = service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            # 找到資料夾，更新 parent_id
            parent_id = items[0]['id']
            print(f"找到資料夾：{folder_name} (ID: {parent_id})")
        else:
            print(f"資料夾路徑不存在：{folder_path}")
            return False

    print(f"完整資料夾路徑存在：{folder_path} (最終 ID: {parent_id})")
    return True

def list_root_files(creds):
    # 建立 Drive API 服務物件
    service = build('drive', 'v3', credentials=creds)

    # 設定搜尋條件：
    # 'root' in parents 表示父目錄是根目錄
    # trashed = false 表示排除垃圾桶
    query = "'root' in parents and trashed = false"

    results = service.files().list(
        q=query,
        pageSize=100,  # 每次抓取的數量上限
        fields="nextPageToken, files(id, name, mimeType)" # 指定回傳欄位
    ).execute()

    items = results.get('files', [])

    if not items:
        print('根目錄下沒有任何檔案。')
    else:
        print('--- 根目錄下的資料清單 ---')
        for item in items:
            # 辨識是資料夾還是檔案
            file_type = "[資料夾]" if item['mimeType'] == 'application/vnd.google-apps.folder' else "[檔案  ]"
            print(f"{file_type} 名稱：{item['name']} (ID: {item['id']})")

    return items

def list_folder_files(creds, folder_id):
    # 建立 Drive API 服務物件
    service = build('drive', 'v3', credentials=creds)

    # 設定搜尋條件：
    # 'folder_id' in parents 表示父目錄是指定的資料夾
    # trashed = false 表示排除垃圾桶
    query = f"'{folder_id}' in parents and trashed = false"

    results = service.files().list(
        q=query,
        pageSize=100,  # 每次抓取的數量上限，
        supportsAllDrives=True,         # 必備：允許存取共用硬碟內容
    includeItemsFromAllDrives=True,     # 必備：搜尋範圍包含共用硬碟
        fields="nextPageToken, files(id, name, mimeType)" # 指定回傳欄位
    ).execute()

    items = results.get('files', [])

    if not items:
        print(f'資料夾 ID {folder_id} 下沒有任何檔案。')
    else:
        print(f'--- 資料夾 ID {folder_id} 下的資料清單 ---')
        for item in items:
            # 辨識是資料夾還是檔案
            file_type = "[資料夾]" if item['mimeType'] == 'application/vnd.google-apps.folder' else "[檔案  ]"
            print(f"{file_type} 名稱：{item['name']} (ID: {item['id']})")

    return items

def list_shared_drives(creds):
    service = build('drive', 'v3', credentials=creds)
    
    # 列出所有你有權限存取的 Shared Drive
    results = service.drives().list(pageSize=50).execute()
    shared_drives = results.get('drives', [])
    
    if not shared_drives:
        print('找不到任何共用雲端硬碟。')
    else:
        for drive in shared_drives:
            print(f"名稱：{drive['name']} (ID: {drive['id']})")
    return shared_drives

def list_files_in_shared_drive(shared_drive_id, creds):
    service = build('drive', 'v3', credentials=creds)

    # 關鍵參數：
    # 1. q 條件中使用共用硬碟的 ID
    # 2. supportsAllDrives=True (必須)
    # 3. includeItemsFromAllDrives=True (必須)
    # 4. corpora='drive' 並且指定 driveId (推薦，這會縮小搜尋範圍到該硬碟)
    
    query = f"'{shared_drive_id}' in parents and trashed = false"

    results = service.files().list(
        q=query,
        supportsAllDrives=True, 
        includeItemsFromAllDrives=True,
        corpora='drive',
        driveId=shared_drive_id,
        fields="files(id, name, mimeType)"
    ).execute()

    items = results.get('files', [])

    for item in items:
        print(f"{item['name']} ({item['id']})")
        
def upload_to_drive(file_path, folder_id, creds, name=None):
    service = build('drive', 'v3', credentials=creds)
    
    if name is None:
        name, ext = Path(file_path).stem, "".join(Path("archive.tar.gz").suffixes)
    else:
        ext = "".join(Path("archive.tar.gz").suffixes)
    
    file_metadata = {
        'name': f"{name}{ext}",
        'parents': [folder_id] # 這裡放 Shared Drive 裡的資料夾 ID
    }
    
    # ... 設定 media ...
    media = MediaFileUpload(
        file_path, 
        resumable=True         # 開啟續傳功能 (強烈建議，大檔案必備)
    )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        supportsAllDrives=True, # 必須加入此參數
        fields='id'
    ).execute()
    
# --- 使用方式 ---
# folder_id = get_or_create_folder("我的備份資料夾", creds)
# 然後再用這個 folder_id 去執行上傳動作

# 執行
if __name__ == "__main__":
    token_info = get_detailed_token_info()