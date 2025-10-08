import streamlit as st
from openai import OpenAI
import base64
import os
from dotenv import load_dotenv
from PIL import Image
import io
from bs4 import BeautifulSoup
import pathlib

GA_JS = """<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6795406112912342"
     crossorigin="anonymous"></script>"""

# Insert the script in the head tag of the static template inside your virtual environement
index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
soup = BeautifulSoup(index_path.read_text(), features="lxml")
if not soup.find(id='custom-js'):
    script_tag = soup.new_tag("script", id='custom-js')
    script_tag.string = GA_JS
    soup.head.append(script_tag)
    index_path.write_text(str(soup))


#-----------------------------------------------------------------------------------------------


st.write("💸 후원 | 토스뱅크 1908-5007-2520")
st.title("Chat Predicter 💭")
st.write("상대와의 대화내용을 바탕으로 다음 대화를 예측합니다.")
st.caption("절대로 사용자 데이터를 저장하지 않습니다.")
st.caption("대화내용 이외의 비정상적인 이미지 감지 시 부정 이용으로 자동 정지될 수 있습니다.")
st.caption("DM, Kakaotalk, MMS 등 모두 가능합니다!")

uploaded = st.file_uploader("📸 대화내용 스크린샷 순서대로 업로드 (5개까지)", accept_multiple_files=True)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MAX_WIDTH = 1024

if uploaded:
    if len(uploaded) > 5:
        st.error("5개까지만 가능합니다.")
    else:
        message = st.text_input("보내고 싶은 메세지를 입력하세요😏")
        if message:
            contents = []

            for image_file in uploaded:
                # PIL로 이미지 열기
                img = Image.open(image_file)

                # 해상도 제한
                if img.width > MAX_WIDTH:
                    ratio = MAX_WIDTH / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((MAX_WIDTH, new_height))

                # 바이트 변환
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                contents.append({
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{img_base64}"
                })

            response = client.responses.create(
    model="gpt-5-mini",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"""
                            너는 메시지 분석 전문가야.
                            메세지 분석 전문가는 첨부된 이미지를 바탕으로 내가 보낼 메세지에 대한 상대방의 반응을 예측해야해.

                            이미지 분석 방법
                            - 왼쪽 메세지: 상대방이 보낸 것
                            - 오른쪽 메세지: 내가 보낸 것

                            이때 너는 왼쪽사람(상대방)의 입장에서 오른쪽 사람(나)이 보낼 메세지에 대한 반응을 예측해야해.

                            주의할점
                            - 상대방의 말투와 매우 유사하게 말해야함.
                            - 너는 시뮬레이터의 역할을 하는거임.
                            - 출력 형식을 준수해야함.

                            아래 이미지를 읽고, 내가 보낼 메시지에 대한 상대방 반응을 예측해줘.

                            내가 보낼 메시지: "{message}"

                            너의 출력 (무조건 이 형식으로 해야함):
                            1:첨부된 채팅에서 상대의 입장에서 나에대한 호감도 평가 (1~5 자연수)
                            2:예상 답변 예시 2~3개 (콤마로 구분)
                            3:코멘트 (톤/말투/주의점)
                            """
                                            },
                                            *contents,  # 이미지들 추가
                                        ],
                                    }
                                ],
                            )


            # GPT 응답 파싱
            text_output = response.output_text
            lines = [l.strip() for l in text_output.split("\n") if l.strip()]

            if len(lines) >= 3:
                like = int(lines[0].split(":")[1])
                texts = lines[1].split(":")[1].replace('","','"\n')
                comment = lines[2].split(":")[1]

                st.markdown(f"**호감도:** {'♥️'*like + '⭕'*(5-like)}")
                st.chat_message("assistant").markdown(texts)
                st.warning(comment)
            else:
                st.error("출력 형식이 올바르지 않습니다. 모델 응답을 확인하세요.")
