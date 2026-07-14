import { Link, useParams } from "react-router-dom";

import { orchestrationApi, type OrchMessage } from "../../api/orchestration";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { useAsync } from "../../hooks/useAsync";

export function Conversation() {
  const { threadId = "" } = useParams();
  const { data, loading, error } = useAsync<OrchMessage[]>(
    () => orchestrationApi.threadMessages(threadId).then((r) => r.data),
    [threadId],
  );
  if (loading) return <Loading label="Loading conversation…" />;
  if (error) return <ErrorNotice message={error} />;
  const messages = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Conversation</h1>
          <p>Persisted messages for this execution thread (provider-independent).</p>
        </div>
        <Link to="/orchestration/runs" className="btn">
          Executions
        </Link>
      </div>

      {messages.length === 0 ? (
        <Empty message="No messages in this thread." />
      ) : (
        <div className="conversation">
          {messages.map((m) => (
            <div key={m.id} className={`chat-msg chat-${m.role}`}>
              <div className="chat-role">{m.role}</div>
              <div className="chat-content">{m.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
