class LLM:
    """Wraps a Hugging Face chat model for greedy, repeatable drafting."""

    def __init__(self, model_id: str, device: str, dtype: str = "float32") -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_id = model_id
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, dtype=getattr(torch, dtype))
        self.model = self.model.to(self.device)
        self.model.eval()

    def generate(self, messages: list[dict], max_new_tokens: int) -> str:
        import torch

        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
        ).to(self.device)
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        new_tokens = output[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()