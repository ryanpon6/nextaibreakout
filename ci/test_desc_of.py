import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import seo2
def test_hf_model_without_card_text_is_not_empty():
    x = {"id": "hfmodel:a/b", "source": "huggingface", "kind": "model", "what": "", "extra": {"hf_type": "model", "summary": None, "title": None}}
    assert seo2.desc_of(x) == "Hugging Face model (no description on its card)"
def test_real_description_wins():
    assert seo2.desc_of({"id": "gh:x", "source": "github", "kind": "repo", "what": "Real text"}) == "Real text"
if __name__ == "__main__":
    test_hf_model_without_card_text_is_not_empty(); test_real_description_wins(); print("tests ok")
