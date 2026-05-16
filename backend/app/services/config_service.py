import json
import pika
from typing import Optional
from sqlalchemy.orm import Session
from app.models.domain import ModelConfig, PromptConfig
from app.core.config import RABBIT_HOST, RABBIT_PASS, RABBIT_USER
from fastapi import HTTPException

class ConfigService:
    def __init__(self, db: Session):
        self.db = db

    def send_to_broker(self, message: dict, msg_type: str):

        try:
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBIT_HOST, 
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='webhook_queue', durable=True)
            

            channel.basic_publish(
                exchange='',
                routing_key='webhook_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2, 
                    type=msg_type
                )
            )
            connection.close()
        except Exception as e:
            print(f"!!! ОШИБКА RABBITMQ В CONFIG_SERVICE: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Broker error: {str(e)}") from e


    def get_model_config(self, repo_id: Optional[int] = None) -> Optional[ModelConfig]:
        """Получение конфига: сначала ищем кастомный для repo_id, если нет — отдаем дефолт"""
        if repo_id:
            config = self.db.query(ModelConfig).filter_by(repository_id=repo_id).first()
            if config:
                return config

        return self.db.query(ModelConfig).filter_by(repository_id=None).first()

    def update_model_config(self, repo_id: Optional[int], data) -> ModelConfig:
        """Реализация UPSERT для конфигурации модели + нотификация брокера"""
        config = self.db.query(ModelConfig).filter_by(repository_id=repo_id).first()
        
        if not config:
            config = ModelConfig(repository_id=repo_id)
            self.db.add(config)
            self.db.flush() 

        config.model = data.model
        config.max_tokens = data.max_tokens
        config.temperature = data.temperature
        config.num_ctx = data.num_ctx
        config.top_p = data.top_p
        config.repeat_penalty = data.repeat_penalty
        config.seed = data.seed
        config.llm_http_client_timeout = data.llm_http_client_timeout
        config.vcs_http_client_timeout = data.vcs_http_client_timeout
        config.concurrency = data.concurrency

        self.db.commit()
        self.db.refresh(config)

        broker_payload = {
            "repository_id": repo_id,
            "fields": data.model_dump()
        }
        self.send_to_broker(broker_payload, msg_type="model_config_update")

        return config


    def get_prompt_config(self, repo_id: Optional[int] = None) -> Optional[PromptConfig]:
        """Получение промта с фолбэком на дефолт"""
        if repo_id:
            config = self.db.query(PromptConfig).filter_by(repository_id=repo_id).first()
            if config:
                return config
        return self.db.query(PromptConfig).filter_by(repository_id=None).first()

    def update_prompt_config(self, repo_id: Optional[int], data) -> PromptConfig:
        """Реализация UPSERT для промта (mode теперь внутри промта) + нотификация брокера"""
        config = self.db.query(PromptConfig).filter_by(repository_id=repo_id).first()
        
        if not config:
            config = PromptConfig(repository_id=repo_id)
            self.db.add(config)
            self.db.flush()

        config.mode = data.mode
        config.prompt_text = data.prompt_text

        self.db.commit()
        self.db.refresh(config)

        broker_payload = {
            "repository_id": repo_id,
            "fields": data.model_dump()
        }
        self.send_to_broker(broker_payload, msg_type="prompt_config_update")

        return config
    

    def seed_default_model_config(self, raw_data: dict) -> bool:
        """Заливка дефолтного конфига модели, если его еще нет в базе"""
        exists = self.db.query(ModelConfig).filter(ModelConfig.repository_id.is_(None)).first()
        if exists:
            return False

        default_config = ModelConfig(
            repository_id=None,
            model=raw_data.get("model"),
            max_tokens=raw_data.get("max_tokens"),
            temperature=raw_data.get("temperature"),
            num_ctx=raw_data.get("num_ctx"),
            top_p=raw_data.get("top_p"),
            repeat_penalty=raw_data.get("repeat_penalty"),
            seed=raw_data.get("seed"),
            llm_http_client_timeout=raw_data.get("llm_http_client_timeout"),
            vcs_http_client_timeout=raw_data.get("vcs_http_client_timeout"),
            concurrency=raw_data.get("concurrency")
        )
        self.db.add(default_config)
        self.db.commit()
        print(">>> [SEED] Глобальная конфигурация модели успешно инициализирована.")
        return True

    def seed_default_prompt_config(self, raw_data: dict) -> bool:
        """Заливка дефолтного системного промта, если его еще нет в базе"""
        exists = self.db.query(PromptConfig).filter_by(repository_id=None).first()
        if exists:
            return False

        default_prompt = PromptConfig(
            repository_id=None,
            mode=raw_data.get("mode"),
            prompt_text=raw_data.get("prompt_text")
        )
        self.db.add(default_prompt)
        self.db.commit()
        print(">>> [SEED] Глобальный системный промпт успешно инициализирован.")
        return True