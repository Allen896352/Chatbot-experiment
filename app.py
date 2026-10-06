import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime
from openai import OpenAI

# ==========================================
# 網頁基本設定 (必須放在最上方)
# ==========================================
st.set_page_config(
    page_title="AI聊天機器人", # 瀏覽器標籤頁顯示的名稱
    page_icon="💬",          # 瀏覽器標籤頁顯示的圖示 (可放 Emoji)
    layout="centered"
)

# ==========================================
# 透過 Streamlit Secrets 安全地讀取 API Key
# ==========================================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 初始化 session_state 變數，控制實驗流程與儲存資料
if "stage" not in st.session_state:
    st.session_state.stage = "background_survey" 
    st.session_state.hc_score = 0
    st.session_state.q_index = 0
    st.session_state.bot_style = ""
    st.session_state.messages = []
    
    # 預留變數儲存問卷與測驗結果
    st.session_state.prior_experience = ""
    st.session_state.usage_frequency = ""

st.title("AI 聊天機器人溝通風格體驗研究")

# ==========================================
# 階段一：基本背景與使用經驗前測
# ==========================================
if st.session_state.stage == "background_survey":
    st.write("### 第一部分：基本使用經驗")
    st.write("在開始之前，請協助我們了解您過去使用 AI 聊天機器人的經驗。")
    
    exp = st.radio("1. 請問您之前是否使用過 AI 聊天機器人？", ["是", "否"], index=None)
    freq = st.selectbox("2. 如果您曾使用過，請問您的使用頻率大約是？", ["請選擇", "從未使用過", "幾個月一次", "每週大約 1-2 次", "幾乎每天使用"])
    
    st.divider()
    if st.button("下一步，進入情境測驗", type="primary"):
        if exp is None or freq == "請選擇":
            st.warning("⚠️ 請完整填寫以上問題後再進入下一步喔！")
        else:
            st.session_state.prior_experience = exp
            st.session_state.usage_frequency = freq
            st.session_state.stage = "pre_test"
            st.rerun()

# ==========================================
# 階段二：隱蔽前測 (判斷高低語境傾向)
# ==========================================
elif st.session_state.stage == "pre_test":
    st.write("### 第二部分：情境決策小測驗")
    st.write("請根據直覺回答以下日常情境題：")
    
    questions = [
        {"q": "情境一：主管交代任務，你偏好哪種方式？", "lc": "給我清晰的步驟與明確清單。", "hc": "告訴我大方向與背景原因即可。"},
        {"q": "情境二：拒絕朋友邀約，你會怎麼說？", "lc": "我那天剛好有事，去不了。", "hc": "聽起來很棒！但我最近有點忙，我再看看喔。"}
    ]
    
    if st.session_state.q_index < len(questions):
        current_q = questions[st.session_state.q_index]
        
        # 視覺優化：用顏色框把題目包起來
        st.info(f"🤔 **{current_q['q']}**", icon="💡")
        st.write("請點擊最符合您直覺的作法：")
        st.write("") 
        
        col1, col2 = st.columns(2)
        with col1:
            # 視覺優化：加上 use_container_width=True 讓選項按鈕變大
            if st.button(current_q['lc'], key=f"lc_{st.session_state.q_index}", use_container_width=True):
                st.session_state.q_index += 1
                st.rerun()
        with col2:
            if st.button(current_q['hc'], key=f"hc_{st.session_state.q_index}", use_container_width=True):
                st.session_state.hc_score += 1 
                st.session_state.q_index += 1
                st.rerun()
    else:
        # 分派邏輯：隨機分配機器人風格 (模擬實驗 2x2 設計)
        st.session_state.bot_style = random.choice(["高語境 (High-Context)", "低語境 (Low-Context)"])
        st.session_state.stage = "chat_task"
        st.rerun()

# ==========================================
# 階段三：核心對話任務 (真實 AI 串接版 + 防呆按鈕)
# ==========================================
elif st.session_state.stage == "chat_task":
    st.write("### 第三部分：客服互動體驗")
    
    # 增加詳細的情境描述框
    st.info(
        "💡 **【任務情境說明】**\n\n"
        "假設您上週在網路商城買了一副「藍牙耳機」，但收到後發現「右邊的耳機完全沒有聲音」。\n\n"
        "👉 **您的任務：** 請透過下方的對話框，向客服機器人說明商品瑕疵，並**詢問該如何辦理退貨或換貨**。\n\n"
        "*(請盡量像平常遇到客訴情況一樣，自然地與機器人進行對話)*",
        icon="🛍️"
    )
    
    # 1. 根據分派的風格，設定 AI 的「系統人設 (System Prompt)」
    if "system_prompt_set" not in st.session_state:
        if st.session_state.bot_style == "高語境 (High-Context)":
            sys_prompt ="""你是一家網路商城的客服，請嚴格遵循以下「高語境溝通」規則來回覆使用者：
            1. 社交客套與招呼：在解答問題前，必須先進行溫暖的社交問候與閒聊，建立對話關係背景。
            2. 委婉與緩和表達：避免過於直接的拒絕或字眼，改用緩和修飾語、抱歉與同理心詞彙以維持和諧。
            3. 非語言與情感線索：頻繁且適當地融入表情符號（Emojis），模擬人類對話中的面部表情與情緒線索。
            4. 情感協助與共感：表現出主動傾聽與同理心，營造專屬私密對話夥伴的陪伴氛圍與安全空間。
            5. 情境脈絡補充：回覆時適度補充背景原因、故事性說明或關懷提醒，提供豐富的情境資訊。"""
        else:
            sys_prompt = """你是一家網路商城的客服，請嚴格遵循以下「低語境溝通」規則來回覆使用者：
            1. 直接開門見山：省略所有社交閒聊與客套話，第一句話即直接給出問題的核心解答。
            2. 語言明確與精準：用字極度精準、客觀且無模糊空間，所有訊息均明示於文字編碼中，不留言外之意。
            3. 結構化與簡潔版面：善用條列式與清晰結構呈現資訊，方便快速擷取重點。
            4. 客觀與對話控制：保持專業客觀語氣，不添加個人情感評價，給予使用者高度的對話流程掌控權。"""
        
        # 將系統提示詞作為對話的第一句 (隱藏不顯示給使用者看)
        st.session_state.messages.append({"role": "system", "content": sys_prompt})
        st.session_state.system_prompt_set = True

    # 2. 顯示歷史對話紀錄 (略過 system 角色不顯示)
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    # 3. 接收使用者輸入，並呼叫 OpenAI API
    if prompt := st.chat_input("請輸入您的訊息... (例如：你好，我買的耳機壞了)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # 呼叫 OpenAI API (使用 gpt-4o-mini 模型)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
            )
            
            bot_reply = response.choices[0].message.content
            message_placeholder.markdown(bot_reply)
        
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
    st.divider()
    
    # 4. 防呆機制：計算使用者發送的訊息數量 (排除系統與助理訊息)
    user_msg_count = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
    
    # 設定最少需要對話的次數
    MIN_INTERACTIONS = 5
    
    if user_msg_count >= MIN_INTERACTIONS:
        if st.button("✅ 任務已完成，結束對話", type="primary", use_container_width=True):
            st.session_state.stage = "post_test"
            st.rerun()
    else:
        remain = MIN_INTERACTIONS - user_msg_count
        if user_msg_count == 0:
            st.warning(f"👈 請在下方輸入框與客服對話。為確保體驗完整，請至少進行 **{MIN_INTERACTIONS} 次** 訊息傳送。")
        else:
            st.warning(f"💬 對話進行中... 請**再發送 {remain} 則訊息**與機器人互動，結束任務的按鈕就會出現喔！")

# ==========================================
# 階段四：後測問卷與寫入 Excel
# ==========================================
elif st.session_state.stage == "post_test":
    st.write("### 第四部分：互動體驗問卷")
    st.write("請根據剛剛與客服機器人的互動經驗，評估以下描述（1分=非常不同意，7分=非常同意）：")
    
    options = [1, 2, 3, 4, 5, 6, 7]
    
    fit_score = st.radio("1. 這個機器人的溝通方式，很符合我平時習慣的交流模式。(知覺契合度)", options, horizontal=True)
    close_score = st.radio("2. 我覺得這個機器人似乎能理解我、與我有一種親近感。(社會親近感)", options, horizontal=True)
    clarity_score = st.radio("3. 這個機器人傳遞的訊息非常容易理解，沒有模糊地帶。(訊息清晰度)", options, horizontal=True)
    emotion_score = st.radio("4. 這次的互動體驗讓我在情緒上感到很舒適。(情感價值)", options, horizontal=True)
    function_score = st.radio("5. 這個機器人提供的資訊具有高度的實用性。(功能價值)", options, horizontal=True)
    reuse_score = st.radio("6. 未來如果有需求，我會有意願再次使用這個機器人。(再次使用意圖)", options, horizontal=True)
    
    st.divider()
    # === 新增：抽獎機制區塊 ===
    st.write("🎁 **加碼抽獎活動（選填）**")
    st.write("為了感謝您用心完成實驗，我們將抽出幾位幸運兒贈送【超商商品卡 / LINE Points】！")
    contact_info = st.text_input("若您有意願參與抽獎，請留下您的 Email 或 IG 帳號（若不參與請直接留白）：")

    st.divider()

    if st.button("送出問卷並結束實驗", type="primary"):
        # 1. 判斷使用者的傾向與適配情況
        user_style = "高語境 (High-Context)" if st.session_state.hc_score >= 1 else "低語境 (Low-Context)"
        is_matched = "適配 (Matched)" if user_style == st.session_state.bot_style else "不適配 (Mismatched)"
        
        # 2. 整理要存入 Excel 的這筆資料 (中文標題)
        result_data = {
            "填答時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "是否有使用經驗": st.session_state.prior_experience,
            "使用頻率": st.session_state.usage_frequency,
            "前測高語境分數": st.session_state.hc_score,
            "判定使用者風格": user_style,
            "分派機器人風格": st.session_state.bot_style,
            "適配情況": is_matched,
            "知覺溝通契合度": fit_score,
            "知覺社會親近感": close_score,
            "知覺訊息清晰度": clarity_score,
            "情感價值": emotion_score,
            "功能價值": function_score,
            "再次使用意圖": reuse_score
        }
        
        # 3. 寫入 Excel 的邏輯
        file_name = "experiment_results.xlsx"
        df_new = pd.DataFrame([result_data])
        
        if os.path.exists(file_name):
            df_existing = pd.read_excel(file_name)
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            df_final.to_excel(file_name, index=False)
        else:
            df_new.to_excel(file_name, index=False)
            
        st.session_state.stage = "finish"
        st.rerun()

# ==========================================
# 結束畫面
# ==========================================
elif st.session_state.stage == "finish":
    st.success("🎉 資料已成功儲存！非常感謝您的參與！")
    st.write("您的回覆已經記錄完成了。")
    
    if st.button("重新開始一筆新測試"):
        st.session_state.clear()
        st.rerun()

# ==========================================
# 管理員後台：下載 Excel 資料 (放在側邊欄)
# ==========================================
with st.sidebar:
    st.write("### 🔒 研究者管理後台")
    admin_password = st.text_input("請輸入管理員密碼", type="password")
    
    # 這裡的密碼請在下方自行設定，目前預設為 "1234"
    if admin_password == "1234":
        st.success("密碼正確！")
        file_name = "experiment_results.xlsx"
        
        if os.path.exists(file_name):
            with open(file_name, "rb") as file:
                btn = st.download_button(
                    label="📥 下載實驗數據 (Excel)",
                    data=file,
                    file_name=f"實驗結果_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("目前還沒有人填寫，尚無資料可下載。")
