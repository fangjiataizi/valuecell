"""Trading configuration management API - for creating and managing trading configurations"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading/config", tags=["trading-config"])

# Storage file path
CONFIG_STORAGE_PATH = Path("/tmp/valuecell_trading_configs.json")


class TradingConfigCreate(BaseModel):
    """Trading configuration creation model"""

    name: str = Field(..., description="Configuration name")
    crypto_symbols: List[str] = Field(..., description="List of crypto symbols to trade")
    initial_capital: float = Field(..., gt=0, description="Initial capital in USD")
    check_interval: int = Field(default=60, ge=10, description="Check interval in seconds")
    use_ai_signals: bool = Field(default=True, description="Enable AI trading signals")
    agent_models: List[str] = Field(..., description="List of AI model IDs to use")
    risk_per_trade: float = Field(default=0.02, ge=0, le=1, description="Risk per trade (0-1)")
    max_positions: int = Field(default=3, ge=1, le=10, description="Maximum positions")


class TradingConfigResponse(TradingConfigCreate):
    """Trading configuration response model"""

    id: str
    created_at: str
    updated_at: str
    active_instances: List[str] = Field(default_factory=list)


class TradingConfigUpdate(BaseModel):
    """Trading configuration update model"""

    name: Optional[str] = None
    crypto_symbols: Optional[List[str]] = None
    initial_capital: Optional[float] = Field(None, gt=0)
    check_interval: Optional[int] = Field(None, ge=10)
    use_ai_signals: Optional[bool] = None
    agent_models: Optional[List[str]] = None
    risk_per_trade: Optional[float] = Field(None, ge=0, le=1)
    max_positions: Optional[int] = Field(None, ge=1, le=10)


def _load_configs() -> Dict[str, Any]:
    """Load configurations from storage"""
    if not CONFIG_STORAGE_PATH.exists():
        return {"configs": [], "instances": {}}
    
    try:
        with open(CONFIG_STORAGE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configs: {e}")
        return {"configs": [], "instances": {}}


def _save_configs(data: Dict[str, Any]) -> None:
    """Save configurations to storage"""
    try:
        CONFIG_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_STORAGE_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {e}")


@router.post("/create", response_model=TradingConfigResponse)
async def create_config(config: TradingConfigCreate) -> TradingConfigResponse:
    """
    创建新的交易配置
    
    Args:
        config: Trading configuration data
        
    Returns:
        Created configuration with ID
    """
    # Validate models
    if not config.agent_models:
        raise HTTPException(
            status_code=400, detail="至少需要选择一个 AI 模型"
        )
    
    # Load existing configs
    data = _load_configs()
    configs = data.get("configs", [])
    
    # Create new config
    config_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    new_config = {
        "id": config_id,
        "name": config.name,
        "crypto_symbols": config.crypto_symbols,
        "initial_capital": config.initial_capital,
        "check_interval": config.check_interval,
        "use_ai_signals": config.use_ai_signals,
        "agent_models": config.agent_models,
        "risk_per_trade": config.risk_per_trade,
        "max_positions": config.max_positions,
        "created_at": now,
        "updated_at": now,
        "active_instances": [],
    }
    
    configs.append(new_config)
    data["configs"] = configs
    _save_configs(data)
    
    logger.info(f"Created trading config: {config_id} - {config.name}")
    
    return TradingConfigResponse(**new_config)


@router.get("/list", response_model=List[TradingConfigResponse])
async def list_configs() -> List[TradingConfigResponse]:
    """
    获取所有交易配置列表
    
    Returns:
        List of trading configurations
    """
    data = _load_configs()
    configs = data.get("configs", [])
    
    # Update active instances from trading data
    try:
        trading_data_path = Path("/tmp/valuecell_trading_data.json")
        if trading_data_path.exists():
            with open(trading_data_path, "r") as f:
                trading_data = json.load(f)
            
            # Map instance to config (by matching symbols and models)
            config_to_instances = {}
            for instance in trading_data.get("instances", []):
                inst_config = instance.get("config", {})
                inst_symbols = set(inst_config.get("crypto_symbols", []))
                inst_models = inst_config.get("agent_model", "")
                
                # Find matching config
                for cfg in configs:
                    cfg_symbols = set(cfg.get("crypto_symbols", []))
                    cfg_models = cfg.get("agent_models", [])
                    
                    if inst_symbols == cfg_symbols and inst_models in cfg_models:
                        cfg_id = cfg["id"]
                        if cfg_id not in config_to_instances:
                            config_to_instances[cfg_id] = []
                        config_to_instances[cfg_id].append(instance.get("instance_id", ""))
            
            # Update active instances
            for cfg in configs:
                cfg["active_instances"] = config_to_instances.get(cfg["id"], [])
    except Exception as e:
        logger.debug(f"Failed to update active instances: {e}")
    
    return [TradingConfigResponse(**cfg) for cfg in configs]


@router.get("/{config_id}", response_model=TradingConfigResponse)
async def get_config(config_id: str) -> TradingConfigResponse:
    """
    获取特定配置详情
    
    Args:
        config_id: Configuration ID
        
    Returns:
        Configuration details
    """
    data = _load_configs()
    configs = data.get("configs", [])
    
    for cfg in configs:
        if cfg["id"] == config_id:
            return TradingConfigResponse(**cfg)
    
    raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")


@router.put("/{config_id}", response_model=TradingConfigResponse)
async def update_config(
    config_id: str, update: TradingConfigUpdate
) -> TradingConfigResponse:
    """
    更新交易配置
    
    Args:
        config_id: Configuration ID
        update: Updated configuration fields
        
    Returns:
        Updated configuration
    """
    data = _load_configs()
    configs = data.get("configs", [])
    
    for i, cfg in enumerate(configs):
        if cfg["id"] == config_id:
            # Update fields
            update_dict = update.model_dump(exclude_unset=True)
            cfg.update(update_dict)
            cfg["updated_at"] = datetime.now().isoformat()
            
            data["configs"] = configs
            _save_configs(data)
            
            logger.info(f"Updated trading config: {config_id}")
            return TradingConfigResponse(**cfg)
    
    raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")


@router.delete("/{config_id}")
async def delete_config(config_id: str) -> Dict[str, Any]:
    """
    删除交易配置
    
    Args:
        config_id: Configuration ID
        
    Returns:
        Success message
    """
    data = _load_configs()
    configs = data.get("configs", [])
    
    original_count = len(configs)
    configs = [cfg for cfg in configs if cfg["id"] != config_id]
    
    if len(configs) == original_count:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
    
    data["configs"] = configs
    _save_configs(data)
    
    logger.info(f"Deleted trading config: {config_id}")
    
    return {"success": True, "message": f"Configuration {config_id} deleted"}


@router.post("/{config_id}/start")
async def start_trading_from_config(config_id: str) -> Dict[str, Any]:
    """
    从配置启动交易实例
    
    这个端点会将配置信息发送给 AutoTradingAgent
    实际启动需要通过 WebSocket 或 HTTP 调用 AutoTradingAgent
    
    Args:
        config_id: Configuration ID
        
    Returns:
        Success message and instructions
    """
    # Get configuration
    data = _load_configs()
    configs = data.get("configs", [])
    
    config = None
    for cfg in configs:
        if cfg["id"] == config_id:
            config = cfg
            break
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
    
    # Build trading request format
    trading_request = {
        "crypto_symbols": config["crypto_symbols"],
        "initial_capital": config["initial_capital"],
        "use_ai_signals": config["use_ai_signals"],
        "agent_models": config["agent_models"],
    }
    
    logger.info(f"Starting trading from config {config_id}: {config['name']}")
    
    return {
        "success": True,
        "config_id": config_id,
        "config_name": config["name"],
        "trading_request": trading_request,
        "message": "配置已准备，请通过 AutoTradingAgent 启动交易",
        "note": "实际启动需要调用 AutoTradingAgent 的 stream 方法",
    }


@router.get("/models/available")
async def get_available_models() -> List[Dict[str, Any]]:
    """
    获取可用的 AI 模型列表
    
    Returns:
        List of available models
    """
    models = []
    
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        models.extend([
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "provider": "openai",
                "type": "chat",
            },
            {
                "id": "gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "provider": "openai",
                "type": "chat",
            },
        ])
    
    # Check Qwen (DashScope)
    if os.getenv("DASHSCOPE_API_KEY"):
        models.extend([
            {
                "id": "qwen-plus",
                "name": "Qwen Plus",
                "provider": "qwen",
                "type": "chat",
            },
            {
                "id": "qwen-max",
                "name": "Qwen Max",
                "provider": "qwen",
                "type": "chat",
            },
        ])
    
    # Check DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        models.extend([
            {
                "id": "deepseek/deepseek-v3.1-terminus",
                "name": "DeepSeek V3.1 Terminus",
                "provider": "deepseek",
                "type": "chat",
            },
            {
                "id": "deepseek/deepseek-chat",
                "name": "DeepSeek Chat",
                "provider": "deepseek",
                "type": "chat",
            },
        ])
    
    # Check OpenRouter (if configured)
    if os.getenv("OPENROUTER_API_KEY"):
        models.extend([
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet (via OpenRouter)",
                "provider": "openrouter",
                "type": "chat",
            },
        ])
    
    return models


@router.get("/templates/list")
async def get_config_templates() -> List[Dict[str, Any]]:
    """
    获取配置模板列表
    
    Returns:
        List of configuration templates
    """
    templates = [
        {
            "id": "conservative",
            "name": "保守策略",
            "description": "低风险，单笔风险 1%，最大持仓 2",
            "risk_per_trade": 0.01,
            "max_positions": 2,
            "recommended_models": ["qwen-plus", "gpt-4o"],
        },
        {
            "id": "balanced",
            "name": "平衡策略",
            "description": "中等风险，单笔风险 2%，最大持仓 3",
            "risk_per_trade": 0.02,
            "max_positions": 3,
            "recommended_models": ["deepseek/deepseek-v3.1-terminus", "qwen-max"],
        },
        {
            "id": "aggressive",
            "name": "激进策略",
            "description": "高风险，单笔风险 5%，最大持仓 5",
            "risk_per_trade": 0.05,
            "max_positions": 5,
            "recommended_models": ["deepseek/deepseek-v3.1-terminus"],
        },
    ]
    
    return templates

