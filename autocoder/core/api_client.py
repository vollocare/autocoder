"""
API client for the Qwen 2.5 Coder model.
"""

import json
import time
from typing import Dict, Any, List, Optional
import httpx

from autocoder.utils.config import config
from autocoder.utils.logger import logger


class APIClient:
    """Client for interacting with the Qwen 2.5 Coder model API."""
    
    def __init__(self, api_endpoint: Optional[str] = None):
        self.api_endpoint = api_endpoint or config.get("model.api_endpoint")
        self.client = httpx.Client(timeout=240.0)  # Extended timeout for model inference
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for API requests."""
        return {
            "Content-Type": "application/json",
        }
    
    def _build_message_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        seed: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build the payload for a model API request."""
        temperature = temperature if temperature is not None else config.get("model.temperature")
        top_p = top_p if top_p is not None else config.get("model.top_p")
        max_tokens = max_tokens if max_tokens is not None else config.get("model.max_tokens")
        seed = seed if seed is not None else config.get("model.seed")
        system_prompt = system_prompt if system_prompt is not None else config.get("model.system_prompt")
        
        payload = {
            "model": "qwen2.5-coder-32b-instruct-mlx",
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        if system_prompt:
            # If a message with role=system is not already in messages, add it
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": system_prompt})
        
        return payload
    
    def generate_code(
        self,
        prompt: str,
        context: Optional[str] = None,
        repo_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> str:
        """
        Generate code using the Qwen 2.5 Coder model.
        
        Args:
            prompt: The main prompt describing the code to generate
            context: Additional context information like error messages
            repo_context: Repository context in Qwen 2.5 Coder format
            system_prompt: System prompt to guide the model's behavior
            temperature: Sampling temperature (0.0-1.0)
            max_retries: Maximum number of retries on failure
            retry_delay: Initial delay between retries in seconds
            
        Returns:
            str: The generated code
        """
        messages = []
        
        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 估算token數量 (粗略估計為每4個字符約為1個token)
        TOKEN_LIMIT = 32000  # Qwen2.5-coder-32b 可能的最大上下文長度
        ESTIMATED_CHAR_PER_TOKEN = 4
        available_tokens = TOKEN_LIMIT - (len(system_prompt or "") // ESTIMATED_CHAR_PER_TOKEN) - (len(prompt) // ESTIMATED_CHAR_PER_TOKEN) - 500  # 保留安全空間
        
        # 限制repo_context的大小
        if repo_context and len(repo_context) > available_tokens * ESTIMATED_CHAR_PER_TOKEN:
            logger.warning(f"Repository context too large ({len(repo_context) // ESTIMATED_CHAR_PER_TOKEN} tokens), truncating to ~{available_tokens} tokens")
            # 保留開頭的 repo_name 部分
            repo_name_end = repo_context.find("\n<|file_sep|>")
            if repo_name_end > 0:
                repo_name_part = repo_context[:repo_name_end+1]
                files_part = repo_context[repo_name_end+1:]
                
                # 只保留前面部分的文件
                files = []
                current_file = ""
                for line in files_part.splitlines():
                    if line.startswith("<|file_sep|>"):
                        if current_file:
                            files.append(current_file)
                        current_file = line + "\n"
                    else:
                        current_file += line + "\n"
                if current_file:
                    files.append(current_file)
                
                # 計算每個文件的長度
                file_lengths = [(i, len(f)) for i, f in enumerate(files)]
                file_lengths.sort(key=lambda x: x[1], reverse=True)  # 按大小排序
                
                # 移除最大的文件，直到大小符合要求
                remaining_chars = available_tokens * ESTIMATED_CHAR_PER_TOKEN - len(repo_name_part)
                included_indices = set(range(len(files)))
                for i, length in file_lengths:
                    if sum(len(files[j]) for j in included_indices) <= remaining_chars:
                        break
                    if i in included_indices:
                        included_indices.remove(i)
                
                # 重建上下文
                new_repo_context = repo_name_part
                for i in sorted(included_indices):  # 按原始順序添加
                    new_repo_context += files[i]
                
                repo_context = new_repo_context
                logger.debug(f"Truncated repository context to {len(repo_context)} chars (~{len(repo_context) // ESTIMATED_CHAR_PER_TOKEN} tokens)")
        
        # Combine repository context and error context if both are provided
        combined_context = ""
        if repo_context:
            combined_context = repo_context
            
        if context:
            if combined_context:
                combined_context += "\n\n" + context
            else:
                combined_context = context
        
        # 檢查combined_context的大小
        if combined_context and len(combined_context) > available_tokens * ESTIMATED_CHAR_PER_TOKEN:
            logger.warning(f"Combined context too large ({len(combined_context) // ESTIMATED_CHAR_PER_TOKEN} tokens), truncating to ~{available_tokens} tokens")
            combined_context = combined_context[:available_tokens * ESTIMATED_CHAR_PER_TOKEN]
        
        # Add combined context as a user message if available
        if combined_context:
            messages.append({"role": "user", "content": combined_context})
        
        # Add the main prompt
        messages.append({"role": "user", "content": prompt})
        
        # Try to get a response with retries
        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending request to API (attempt {attempt + 1}/{max_retries})")
                
                response = self.chat_completion(messages, temperature=temperature)
                
                if not response:
                    logger.warning("Received empty response from API")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return ""
                
                logger.debug("Received response from API")
                return response
            
            except Exception as e:
                logger.error(f"API request failed: {str(e)}")
                
                # 如果是上下文長度錯誤，嘗試減少上下文大小
                if "context length" in str(e).lower():
                    logger.warning("Context length error detected, reducing context size for next attempt")
                    
                    # 如果有repo_context並且嘗試次數少於最大重試次數，則減少repo_context的大小
                    if repo_context and attempt < max_retries - 1:
                        # 減少一半的repo_context
                        repo_name_end = repo_context.find("\n<|file_sep|>")
                        if repo_name_end > 0:
                            repo_name_part = repo_context[:repo_name_end+1]
                            new_size = (len(repo_context) - len(repo_name_part)) // 2
                            repo_context = repo_name_part + repo_context[repo_name_end+1:repo_name_end+1+new_size]
                            
                            # 重建消息
                            combined_context = repo_context
                            if context:
                                combined_context += "\n\n" + context
                            
                            # 更新消息列表
                            messages = [m for m in messages if m["role"] != "user"]
                            if combined_context:
                                messages.append({"role": "user", "content": combined_context})
                            messages.append({"role": "user", "content": prompt})
                            
                            logger.debug(f"Reduced repository context to {len(repo_context)} chars")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay *= 1.5
                else:
                    logger.error("Max retries reached, giving up")
                    raise
        
        return ""  # Should not reach here, but just in case
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        seed: Optional[int] = None
    ) -> str:
        """Send a chat completion request to the API."""
        endpoint = f"{self.api_endpoint}/chat/completions"
        headers = self._build_headers()
        
        payload = self._build_message_payload(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            seed=seed
        )
        
        try:
            response = self.client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.warning("Unexpected API response format")
                logger.debug(f"Response: {json.dumps(result)}")
                return ""
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise 