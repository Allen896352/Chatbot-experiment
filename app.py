import streamlit as st
import random
from openai import OpenAI

# ==========================================
# 網頁基本設定 (必須放在最上方)
# ==========================================
st.set_page_config(
    page_title="AI聊天機器人", 
    page_icon="💬",          
    layout="centered"
)

# ==========================================
# 透過 Streamlit Secrets 安全地讀取 API Key
# ==========================================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 初始化 session_state 變數，控制實驗流程
if "stage" not in st.session_state:
    st.session_state.stage = "welcome"  # 初始設定為歡迎與前測頁面
    # 一進來就隨機分配機器人風格
    st.session_state.bot_style =random.choice(["高語境 (High-Context)", "低語境 (Low-Context)"])
    #random.choice(["高語境 (High-Context)", "低語境 (Low-Context)"]) 如果要隨機的話
    st.session_state.messages = []

st.title("AI 聊天機器人溝通風格體驗研究")

# ==========================================
# 階段一：填寫前測 Google 表單
# ==========================================
if st.session_state.stage == "welcome":
    st.write("### 步驟一：填寫基本資料與前測")
    st.write("歡迎參與本次研究！在開始與機器人對話之前，請先點擊下方連結填寫人口統計資料與前測問卷。")
    
    # ⬇️ 預留的前測 Google 表單連結位子 ⬇️
    pre_test_url = "https://forms.gle/YOUR_PRE_TEST_FORM_LINK_HERE"
    st.markdown(f"### [👉 點擊這裡填寫第一部分問卷]({pre_test_url})")
    
    st.info("💡 填寫完畢後，請**保留表單分頁不要關閉**（稍後對話完需繼續填寫），並回到本網頁點擊下方按鈕。")
    
    if st.button("我已完成前測，開始對話任務", type="primary", use_container_width=True):
        st.session_state.stage = "chat_task"
        st.rerun()

# ==========================================
# 階段二：核心對話任務 (真實 AI 串接版)
# ==========================================
elif st.session_state.stage == "chat_task":
    st.write("### 步驟二：客服互動體驗")
    
    # 詳細的情境描述框
    st.info(
        "💡 **【任務情境說明】**\n\n"
        "假設您上週在網路商城買了一件「衣服」，但收到包裹後發現「衣服上有明顯的瑕疵（例如破洞或大片污漬）」。\n\n"
        "👉 **您的任務：** 請透過下方的對話框，向客服機器人說明商品狀況，並**詢問該如何辦理退貨或換貨**。\n\n"
        "*(請盡量像平常遇到客訴情況一樣，自然地與機器人進行對話)*",
        icon="👕"
    )
    
    # 1. 根據分派的風格，設定 AI 的「系統人設 (System Prompt)」
    if "system_prompt_set" not in st.session_state:
        if st.session_state.bot_style == "高語境 (High-Context)":
            sys_prompt = """你是一家網路商城的客服，請嚴格遵循以下「高語境溝通」規則來回覆使用者：
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
    if prompt := st.chat_input("請輸入您的訊息... (例如：你好，我收到的衣服上面有破洞)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # 呼叫 OpenAI API (加入 temperature 參數控制風格穩定性)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.3
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
        if st.button("✅ 任務已完成，結束對話並前往後測問卷", type="primary", use_container_width=True):
            st.session_state.stage = "finish"
            st.rerun()
    else:
        remain = MIN_INTERACTIONS - user_msg_count
        if user_msg_count == 0:
            st.warning(f"👈 請在下方輸入框與客服對話。為確保體驗完整，請至少進行 **{MIN_INTERACTIONS} 次** 訊息傳送。")
        else:
            st.warning(f"💬 對話進行中... 請**再發送 {remain} 則訊息**與機器人互動，結束任務的按鈕就會出現喔！")

# ==========================================
# 階段三：結束畫面與跳轉 Google 表單後測
# ==========================================
elif st.session_state.stage == "finish":
    st.success("🎉 對話任務已完成！非常感謝您的配合。")
    st.write("### 步驟三：完成後測問卷")
    st.write("接下來請點擊下方連結（或回到剛剛未關閉的表單分頁），接續完成最後的後測問題：")
    
    # ⬇️ 預留的後測 Google 表單連結位子 ⬇️
    post_test_url = "https://forms.gle/YOUR_POST_TEST_FORM_LINK_HERE"
    st.markdown(f"### [👉 點擊這裡繼續完成 Google 表單]({post_test_url})")
    
    # 告知使用者他們剛才測驗的語境，方便他們填答問卷
    #st.info(f"💡 提醒：您剛才體驗的機器人風格為 **{st.session_state.bot_style}**。若問卷中有詢問，請以此為準填寫喔！")
    
    st.divider()
    
    if st.button("重新開始一筆新測試"):
        st.session_state.clear()
        st.rerun()
