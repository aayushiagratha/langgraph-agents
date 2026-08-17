from unittest.mock import MagicMock, patch

import brand_voice.persist as persist


def make_mock_conn():
    mock_cur = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = False
    return mock_conn, mock_cur


def test_persist_results_inserts_audit_and_rewrite_rows_and_commits():
    mock_conn, mock_cur = make_mock_conn()
    with patch("brand_voice.persist.get_connection", return_value=mock_conn):
        persist.persist_results(
            generation_run_id="run-123",
            content_type="email",
            audit_output={"compliance_score": 80},
            rewrite_output={"rewritten_content": "x"},
        )

    mock_cur.execute.assert_called_once()
    sql, params = mock_cur.execute.call_args.args
    assert "brand_voice_runs" in sql
    # both rows share the same run id; audit row before rewrite row
    assert params[0] == "run-123"  # audit run id
    assert params[3] == "email"    # audit content_type
    assert params[4] == "run-123"  # rewrite run id
    assert params[7] == "email"    # rewrite content_type
    mock_conn.commit.assert_called_once()
