from brand_voice.prompts import audit_user_prompt, rewrite_user_prompt


def test_audit_user_prompt_embeds_all_inputs():
    p = audit_user_prompt("Be friendly.", "email", "Hey there, buy our stuff now!!")
    assert "Be friendly." in p
    assert "email" in p
    assert "Hey there, buy our stuff now!!" in p


def test_audit_user_prompt_defaults_missing_content_type():
    p = audit_user_prompt("Be friendly.", "", "content")
    assert "general" in p


def test_rewrite_user_prompt_embeds_all_inputs():
    p = rewrite_user_prompt("Be friendly.", "landing page", "Buy now!!")
    assert "Be friendly." in p
    assert "landing page" in p
    assert "Buy now!!" in p
