import streamlit as st
import streamlit.components.v1 as components
import uuid
import random
from openai import OpenAI
import urllib.parse  # 用來處理中文網址編碼

# ==========================================
# 網頁基本設定 (必須放在最上方)
# ==========================================
st.set_page_config(
    page_title="AI 客服互動體驗研究", 
    page_icon="💬",          
    layout="centered"
)

# 透過 Streamlit Secrets 讀取 API Key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 初始化 session_state 變數，控制實驗流程與儲存資料
if "stage" not in st.session_state:
    st.session_state.stage = "consent"  # ⚠️ 初始階段改為：知情同意書
    st.session_state.user_id = str(uuid.uuid4())[:8] # 產生 8 碼的專屬受測者 ID
    st.session_state.hc_score = 0
    st.session_state.lc_score = 0
    st.session_state.bot_style = ""
    st.session_state.messages = []

# ==========================================
# 階段零：知情同意書 (新增區塊)
# ==========================================
if st.session_state.stage == "consent":
    st.title("📝 AI 聊天機器人回覆風格與使用者互動體驗調查")
    
    # 使用 container 排版文字，加上淡淡的邊框增加正式感
    with st.container(border=True):
        st.markdown("""
        **同學您好：**
        
        這是一份由企業管理系學生製作的調查問卷，主要希望透過本問卷探討 AI 聊天機器人溝通風格與使用者語境傾向契合度對再次使用意圖之影響，調查對象為不限年齡之全體民眾。問卷內容共 8 個區段，約需 5-10 分鐘，感謝您撥冗填答。
        
        本問卷採不記名及無法辨識個人的方式作答，電子資料保存至整個研究後即銷毀。研究團隊將盡力維護您的隱私及善盡保密責任，您所提供的所有資料皆嚴格保密。本研究填寫亦不會影響個人成績。
        
        此研究未來發表採整體分析，您不會被辨識出，將發表於學位論文，亦無衍生的商業利益。
        
        請您自由決定是否填寫，亦可中途不填寫，無需感到壓力。惟一旦繳交，本問卷無記名且無編碼，研究團隊將無法辨識本問卷，恕無法刪除您填寫的內容。
        
        若您想詢問本問卷內容，或有興趣得知研究結果，此研究將於完成後，歡迎您依照下述聯絡方式索取研究結果摘要。
        （計畫聯絡人：劉瀚澤，Email: 11245019@ntub.edu.tw）
        
        ---
        **台北商業大學企業管理學系**  
        **研究學生：** 彭昱綺、劉瀚澤、邱郁翔  
        **指導教授：** 顏嬿真 老師
        """)
        
    st.write("") # 排版留白
    
    # 同意核取方塊
    agree = st.checkbox("🔴 **以上問卷知情說明：我已閱讀並同意參與本研究**")
    
    # 判斷是否打勾才能進入下一步
    if st.button("下一步：開始填寫語境測試問卷", type="primary", use_container_width=True):
        if agree:
            st.session_state.stage = "pre_test"
            st.rerun()
        else:
            st.error("⚠️ 請先勾選「同意」知情說明，才能開始進行測驗喔！")

# ==========================================
# 階段一：基本資料與語境判斷 (系統自動計分)
# ==========================================
elif st.session_state.stage == "pre_test":
    st.title("🛍️ 網購客服 AI 互動測試")
    st.write("### 步驟一：語境測試問卷")
    st.write("在開始對話前，請先協助我們填寫基本資料與溝通習慣。")
    
    # 1. 建立題庫：標註每題的屬性 (HC=高語境, LC=低語境)，並手動交錯排列
    if "shuffled_questions" not in st.session_state:
        questions = [
            {"id": "q1", "text": "即使別人沒有直接說出來，我也能察覺他們的意思。", "type": "HC"},
            {"id": "q5", "text": "我會盡量把意思表達得清楚而精確。", "type": "LC"},
            {"id": "q2", "text": "我習慣以間接的方式進行溝通。", "type": "HC"},
            {"id": "q6", "text": "我在溝通時重視表達的準確性。", "type": "LC"},
            {"id": "q3", "text": "當被要求明確表達意見時，我有時會以較含蓄或保留的方式回應。", "type": "HC"},
            {"id": "q7", "text": "我傾向以開放、直接的方式與他人溝通。", "type": "LC"},
            {"id": "q4", "text": "我在與他人溝通時，會盡力維持關係的和諧。", "type": "HC"},
            {"id": "q8", "text": "我願意直接向他人分享與自己有關的資訊。", "type": "LC"}
        ]
        st.session_state.shuffled_questions = questions

    # 2. 建立作答表單
    with st.form("context_test_form"):
        # --- 第一部分：人口統計與 AI Chatbot 使用背景 ---
        st.markdown("#### 第一部分：人口統計與 AI Chatbot 使用背景")
        age = st.selectbox("1. 年齡", ["18歲以下", "19–29歲", "30–39歲", "40–49歲", "50歲以上"])
        gender = st.selectbox("2. 性別", ["男性", "女性", "其他", "不願回答"])
        education = st.selectbox("3. 最高學歷", ["高中以下", "高中（職）", "大專校院", "碩士", "博士"])
        bot_freq = st.selectbox("4. AI Chatbot 使用頻率", ["每天", "每週數次", "每月數次", "很少使用", "從未使用"])
        bot_familiarity = st.selectbox("5. 對 AI Chatbot 的熟悉程度", ["非常熟悉", "熟悉", "普通", "不熟悉", "完全不熟悉"])
        
        st.divider() 
        
        # --- 第二部分：語境評估 ---
        st.markdown("#### 第二部分：溝通風格評估")
        st.write("請依照您平時的溝通習慣，選擇最符合您的程度：\n(1 = 非常不同意，2 = 不同意，3 = 普通，4 = 同意，5 = 非常同意)")
        options = [1, 2, 3, 4, 5] 
        responses = {}
        
        for i, q in enumerate(st.session_state.shuffled_questions):
            responses[q["id"]] = st.radio(f"**{i+1}. {q['text']}**", options, horizontal=True)
            st.write("") 
            
        # 表單送出按鈕
        submitted = st.form_submit_button("✅ 送出並開始對話", type="primary", use_container_width=True)
        
        if submitted:
            # 將新的 5 項基本資料存入 session_state
            st.session_state.age = age
            st.session_state.gender = gender
            st.session_state.education = education
            st.session_state.bot_freq = bot_freq
            st.session_state.bot_familiarity = bot_familiarity
            
            hc_total = 0
            lc_total = 0
            
            # 3. 系統自動分類計分
            for q in st.session_state.shuffled_questions:
                score = responses[q["id"]]
                if q["type"] == "HC":
                    hc_total += score
                else:
                    lc_total += score
                    
            st.session_state.hc_score = hc_total
            st.session_state.lc_score = lc_total
            
            # 4. 判定邏輯：強制隨機分配 (A/B Test 實驗組與對照組)
            st.session_state.bot_style = random.choice(["高語境 (High-Context)", "低語境 (Low-Context)"])
                
            st.session_state.stage = "chat_task"
            st.rerun()

# ==========================================
# 階段二：核心對話任務 (依據測驗結果配對)
# ==========================================
elif st.session_state.stage == "chat_task":
    st.write("### 步驟二：客服互動體驗")
    
    st.info(
        "💡 **【任務情境說明】**\n\n"
        "假設您上週在網路商城買了一件「衣服」，但收到包裹後發現「衣服上有明顯的瑕疵（例如破洞或大片污漬）」。\n\n"
        "👉 **您的任務：** 請透過下方的對話框，向客服機器人說明商品狀況，並**詢問該如何辦理退貨或換貨**。\n\n"
        "*(請盡量像平常遇到客訴情況一樣，自然地與機器人進行對話)*",
        icon="👕"
    )
    
    # 1. 根據前測分派的風格，設定 AI 的系統人設
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
        
        st.session_state.messages.append({"role": "system", "content": sys_prompt})
        st.session_state.system_prompt_set = True

    # 2. 顯示對話紀錄
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    # 3. 接收使用者輸入與呼叫 API
    if prompt := st.chat_input("請輸入您的訊息... (例如：你好，衣服有瑕疵要怎麼換)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.3
            )
            bot_reply = response.choices[0].message.content
            message_placeholder.markdown(bot_reply)
        
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
    st.divider()
    
    # 4. 互動次數防呆機制
    user_msg_count = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
    MIN_INTERACTIONS = 1
    
    if user_msg_count >= MIN_INTERACTIONS:
        if st.button("✅ 任務已完成，結束對話並進行問卷", type="primary", use_container_width=True):
            st.session_state.stage = "finish"
            st.rerun()
    else:
        remain = MIN_INTERACTIONS - user_msg_count
        if user_msg_count == 0:
            st.caption(f"👈 請在下方輸入框與客服對話。需至少進行 **{MIN_INTERACTIONS} 次** 訊息傳送才會出現結束按鈕。")
        else:
            st.caption(f"💬 對話進行中... 請**再發送 {remain} 則訊息**與機器人互動。")

# ==========================================
# 階段三：嵌入後測 Google 表單 (自動帶入 9 項變數)
# ==========================================
elif st.session_state.stage == "finish":
    st.success("🎉 對話任務已完成！非常感謝您的配合。")
    st.write("### 步驟三：完成滿意度問卷")
    st.write("請直接在下方框框內填寫最後的問卷，填寫完畢並按下「提交」即完成本次實驗。")
    
    # ⚠️ 視覺防呆提醒
    st.warning("⚠️ **填寫提醒：** 當您滑到表單最下方的「系統專用區」時，請勿修改裡面的任何亂碼與數字，**直接點擊最底部的『提交』按鈕即可！**", icon="🚨")
    
    base_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSewWNdtHlANTFKhX8aitS-NLaYzvU972dkELGW5L8mvlDqQMg/viewform?usp=pp_url&embedded=true"
    
    # 將包含中文或特殊符號的變數，轉換為網址安全格式 (URL Encoding)
    safe_bot_style = urllib.parse.quote(st.session_state.bot_style)
    safe_age = urllib.parse.quote(st.session_state.age)
    safe_gender = urllib.parse.quote(st.session_state.gender)
    safe_education = urllib.parse.quote(st.session_state.education)
    safe_bot_freq = urllib.parse.quote(st.session_state.bot_freq)
    safe_bot_familiarity = urllib.parse.quote(st.session_state.bot_familiarity)
    
    # ⚠️ 已經完美對接你抓出來的 9 個 ID
    post_test_form_url = (
        f"{base_form_url}"
        f"&entry.235439592={st.session_state.user_id}"          # ID 
        f"&entry.291326502={safe_bot_style}"                    # 系統隨機分配風格
        f"&entry.401818618={st.session_state.hc_score}"         # 高語境分
        f"&entry.1146105863={st.session_state.lc_score}"        # 低語境分
        f"&entry.1204605564={safe_age}"                         # 年齡 
        f"&entry.1418272599={safe_gender}"                      # 性別          
        f"&entry.745662331={safe_education}"                    # 最高學歷 
        f"&entry.417434269={safe_bot_freq}"                     # 使用頻率 
        f"&entry.455003621={safe_bot_familiarity}"              # 熟悉程度
    )
    
    # 縮短 iframe 高度至 600，解決提交後的白畫面問題
    components.iframe(post_test_form_url, width=700, height=600, scrolling=True)
    
    st.divider()
    if st.button("重新開始一筆新測試 (僅供測試除錯用)"):
        st.session_state.clear()
        st.rerun()
