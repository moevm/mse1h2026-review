import os
import yaml
from sqlalchemy.orm import Session
from app.services.config_service import ConfigService

def init_default_configs(db: Session):
    config_service = ConfigService(db)
    
    MODEL_FILE_PATH = os.getenv("MODEL_CONFIG_PATH", "/app/config/.ai-review.yaml")
    PROMPT_FILE_PATH = os.getenv("PROMPT_CONFIG_PATH", "/app/config/prompt.md")

    if os.path.exists(MODEL_FILE_PATH):
        with open(MODEL_FILE_PATH, "r", encoding="utf-8") as f:
            raw_yaml = yaml.safe_load(f)
            
            llm_meta = raw_yaml.get("llm", {}).get("meta", {})
            llm_http = raw_yaml.get("llm", {}).get("http_client", {})
            vcs_http = raw_yaml.get("vcs", {}).get("http_client", {})
            core = raw_yaml.get("core", {})
            
            model_data = {
                "model": llm_meta.get("model", "qwen2.5-coder:1.5b"),
                "max_tokens": llm_meta.get("max_tokens", 5000),
                "temperature": llm_meta.get("temperature", 0.3),
                "num_ctx": llm_meta.get("num_ctx", 5000),
                "top_p": llm_meta.get("top_p", 0.9),
                "repeat_penalty": llm_meta.get("repeat_penalty", 1.1),
                "seed": llm_meta.get("seed", 42),
                "llm_http_client_timeout": float(llm_http.get("timeout", 300.0)),
                "vcs_http_client_timeout": float(vcs_http.get("timeout", 120.0)),
                "concurrency": core.get("concurrency", 2)
            }
            
            config_service.seed_default_model_config(model_data)
    else:
        print(f"!!! [WARNING] Главный файл конфигурации не найден по пути: {MODEL_FILE_PATH}")


    if os.path.exists(MODEL_FILE_PATH):
        with open(MODEL_FILE_PATH, "r", encoding="utf-8") as f:
            raw_yaml = yaml.safe_load(f)

            review_mode = raw_yaml.get("review", {}).get("mode", "FULL_FILE_DIFF")
            
        if os.path.exists(PROMPT_FILE_PATH):
            with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as pf:
                prompt_text = pf.read()
        else:
            prompt_text = "Ты — опытный тимлид. Сделай ревью кода."
            print(f"!!! [WARNING] Файл системного промпта не найден: {PROMPT_FILE_PATH}. Используется дефолт.")
            
        prompt_data = {
            "mode": review_mode,
            "prompt_text": prompt_text
        }
        
        config_service.seed_default_prompt_config(prompt_data)