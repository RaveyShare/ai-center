"""数据库迁移。

表名加 agent_ 前缀避免和业务表冲突。
所有 SQL 都是 IF NOT EXISTS，可重复执行。
"""

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS agent_sessions (
        id VARCHAR(36) PRIMARY KEY,
        agent_name VARCHAR(64) NOT NULL,
        status VARCHAR(16) NOT NULL DEFAULT 'active',
        config JSON,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_agent_status (agent_name, status),
        INDEX idx_updated (updated_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_session_events (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(36) NOT NULL,
        seq INT NOT NULL,
        event_type VARCHAR(32) NOT NULL,
        payload JSON NOT NULL,
        created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        UNIQUE KEY uk_session_seq (session_id, seq),
        INDEX idx_session_type (session_id, event_type),
        INDEX idx_created (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]
