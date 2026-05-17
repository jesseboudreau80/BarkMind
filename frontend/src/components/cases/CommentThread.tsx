"use client";

import { useState } from "react";
import { formatRelativeTime } from "@/lib/utils";
import type { Comment } from "@/lib/types";
import { comments as commentsApi } from "@/lib/api";
import Button from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { useAuth } from "@/contexts/AuthContext";
import { MessageSquare } from "lucide-react";

function CommentItem({
  comment,
  caseId,
  onReply,
}: {
  comment: Comment;
  caseId: string;
  onReply: (parentId: string, body: string) => Promise<void>;
}) {
  const [replying, setReplying] = useState(false);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  async function submit() {
    if (!body.trim()) return;
    setLoading(true);
    await onReply(comment.id, body);
    setBody("");
    setReplying(false);
    setLoading(false);
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-xs font-medium text-zinc-300">
            {comment.author_username}
          </span>
          <span className="text-xs text-zinc-600">
            {formatRelativeTime(comment.created_at)}
          </span>
          {user && (
            <button
              onClick={() => setReplying((v) => !v)}
              className="ml-auto text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              Reply
            </button>
          )}
        </div>
        <p className="text-sm text-zinc-200 leading-relaxed">{comment.body}</p>
      </div>

      {/* Replies */}
      {comment.replies.length > 0 && (
        <div className="ml-6 flex flex-col gap-2">
          {comment.replies.map((reply) => (
            <div
              key={reply.id}
              className="bg-zinc-900/40 border border-zinc-800/60 rounded-lg p-3"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-medium text-zinc-400">
                  {reply.author_username}
                </span>
                <span className="text-xs text-zinc-600">
                  {formatRelativeTime(reply.created_at)}
                </span>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">{reply.body}</p>
            </div>
          ))}
        </div>
      )}

      {/* Reply form */}
      {replying && (
        <div className="ml-6 flex flex-col gap-2">
          <Textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write a reply..."
            className="min-h-[72px] text-sm"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={submit} isLoading={loading} disabled={!body.trim()}>
              Reply
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setReplying(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CommentThread({
  caseId,
  initialComments,
}: {
  caseId: string;
  initialComments: Comment[];
}) {
  const [commentList, setCommentList] = useState<Comment[]>(initialComments);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  async function addComment(parentId?: string, replyBody?: string) {
    const text = replyBody ?? body;
    if (!text.trim() || !user) return;
    setLoading(true);
    try {
      await commentsApi.create(caseId, {
        body: text,
        parent_id: parentId,
      });
      const updated = await commentsApi.list(caseId);
      setCommentList(updated);
      if (!parentId) setBody("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {commentList.length === 0 && (
        <p className="text-sm text-zinc-600 italic py-2">
          No community comments yet.
        </p>
      )}

      {commentList.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          caseId={caseId}
          onReply={(parentId, replyBody) => addComment(parentId, replyBody)}
        />
      ))}

      {user ? (
        <div className="border-t border-zinc-800 pt-4 flex flex-col gap-2">
          <Textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Add a community comment..."
            className="min-h-[80px] text-sm"
          />
          <div className="flex justify-end">
            <Button
              size="sm"
              onClick={() => addComment()}
              isLoading={loading}
              disabled={!body.trim()}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Post Comment
            </Button>
          </div>
        </div>
      ) : (
        <div className="border-t border-zinc-800 pt-4">
          <p className="text-sm text-zinc-500">
            <a href="/login" className="text-amber-400 hover:underline">Sign in</a> to comment.
          </p>
        </div>
      )}
    </div>
  );
}
