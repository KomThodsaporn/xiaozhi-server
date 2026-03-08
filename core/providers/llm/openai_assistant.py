import logging
import asyncio
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self, config):
        # รับค่าที่คุณกรอกมาจากหน้าเว็บ
        self.api_key = config.get("api_key")
        self.assistant_id = config.get("assistant_id")
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # เก็บ Thread ID ไว้เพื่อให้บอทจำบทสนทนาต่อเนื่องได้
        self.session_threads = {} 

    async def generate_response(self, messages, session_id, **kwargs):
        try:
            # ดึงคำถามล่าสุดที่ผู้ใช้พูดกับ ESP32
            user_input = messages[-1]['content']
            
            # 1. จัดการ Thread (ถ้าคุยครั้งแรกให้สร้างใหม่)
            if session_id not in self.session_threads:
                thread = await self.client.beta.threads.create()
                self.session_threads[session_id] = thread.id
            
            thread_id = self.session_threads[session_id]

            # 2. ส่งคำถามเข้าไปในสมอง OpenAI
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input
            )

            # 3. สั่งให้ AI เริ่มค้นหาข้อมูลในไฟล์และคิดคำตอบ
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # 4. รอจนกว่า AI จะคิดและค้นหาข้อมูลเสร็จ
            while run.status in ['queued', 'in_progress']:
                await asyncio.sleep(0.5)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

            # 5. ดึงคำตอบที่สมบูรณ์ออกมาส่งให้เสียงพูด (TTS)
            if run.status == 'completed':
                response_msgs = await self.client.beta.threads.messages.list(thread_id=thread_id)
                answer = response_msgs.data[0].content[0].text.value
                
                # ส่งคำตอบกลับไปให้ XiaoZhi นำไปพูด
                yield answer
            else:
                yield "ขออภัยครับ เกิดข้อผิดพลาดในการค้นหาข้อมูล"

        except Exception as e:
            logger.error(f"OpenAI Assistant Error: {e}")
            yield "ขออภัยครับ ระบบฐานความรู้ขัดข้องชั่วคราว"
