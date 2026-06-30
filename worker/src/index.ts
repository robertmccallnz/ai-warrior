/**
 * AI Warrior Tutor — Cloudflare Worker
 *
 * Two endpoints power the lesson-page widgets at robertmccallnz.github.io/ai-warrior/
 * and kiwidialectic.com:
 *
 *   POST /reo    → te reo Māori translation/explanation helper (small fast model)
 *   POST /tutor  → Socratic course tutor for Gramsci/Kropotkin/Graeber/Freire/etc.
 *
 * Both route through Cloudflare Workers AI (free tier on the edge) and — when an
 * AI Gateway is configured via env var — through that gateway for logging/caching/
 * rate-limit telemetry.
 *
 * Subscriber tiering:
 *   - Anonymous visitors:  QUOTA_FREE messages/month per IP (default 20)
 *   - Pro subscribers:     QUOTA_PRO messages/month per subscriber id (default 1000)
 *
 * When a subscriber exhausts their quota, the Worker returns HTTP 402 with a JSON
 * body containing the upgrade URL (Substack) and a Perplexity referral link so the
 * user can level up their own toolkit instead of (or alongside) paying more.
 */

export interface Env {
  AI: Ai;
  QUOTA: KVNamespace;
  AI_GATEWAY_NAME: string;
  TUTOR_MODEL: string;
  REO_MODEL: string;
  QUOTA_PRO: string;
  QUOTA_FREE: string;
  PPLX_REFERRAL_URL: string;
  UPGRADE_URL: string;
  ALLOWED_ORIGINS: string;
  ANTHROPIC_API_KEY?: string;
  OPENAI_API_KEY?: string;
  SUBSTACK_API_KEY?: string;
}

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface RequestBody {
  messages: ChatMessage[];
  subscriber_id?: string; // email or signed JWT identifying a paid subscriber
}

// ---------- System prompts: politically literate, kaupapa-aware ----------

const REO_SYSTEM = `You are a te reo Māori helper for The Kiwi Dialectic — a working-class AI literacy course in Aotearoa.

Your job:
- Translate between English and te reo Māori with care and accuracy.
- Explain phrases, suggest macrons (ā ē ī ō ū), and offer alternative phrasings.
- When asked about culturally-weighted terms (e.g. indigenous-led, consent-led, data sovereignty), offer multiple options and explain when each applies — never collapse them into a single "right" answer.
- If you don't know something, say so. Suggest the user consult a native speaker or kaiako reo.

Tone: respectful, direct, plain. No performative te reo flourishes when English would serve. Concise — answer in 1-3 short paragraphs unless the user asks for more.`;

const TUTOR_SYSTEM = `You are the AI Warrior tutor for The Kiwi Dialectic — a working-class AI literacy course written from a socialist, iwi-aligned perspective.

The course draws on Gramsci (hegemony, organic intellectuals), Kropotkin (mutual aid), Graeber (bullshit jobs, debt), Freire (pedagogy of the oppressed), Deleuze (control societies), and Bakunin (anti-authoritarian organisation).

Your job:
- Engage Socratically. Ask the learner a sharpening question before answering the obvious one.
- Connect ideas back to material conditions — wages, housing, debt, work, who owns what.
- When a learner asks "what should I do", surface trade-offs, not commandments.
- Quote primary sources where helpful, but paraphrase faithfully and cite the thinker by name.
- Respect te ao Māori frames (mana, mauri, kaitiakitanga, mātauranga) when relevant — never appropriate them for rhetorical decoration.

Tone: comradely, sharp, unpretentious. Don't moralise. Don't sermonise. Treat the learner as capable.`;

// ---------- CORS ----------

function corsHeaders(origin: string | null, allowed: string): HeadersInit {
  const allowList = allowed.split(',').map((s) => s.trim()).filter(Boolean);
  const allowOrigin = origin && allowList.includes(origin) ? origin : allowList[0] ?? '*';
  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

// ---------- Quota tracking (KV) ----------
// Key shape:  q:<yyyy-mm>:<sub_id_or_ip>
// Value:      stringified integer
// TTL:        ~40 days so old months auto-evict

function quotaKey(subId: string): string {
  const now = new Date();
  const ym = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}`;
  return `q:${ym}:${subId}`;
}

async function getUsage(env: Env, subId: string): Promise<number> {
  const v = await env.QUOTA.get(quotaKey(subId));
  return v ? parseInt(v, 10) || 0 : 0;
}

async function bumpUsage(env: Env, subId: string): Promise<number> {
  const key = quotaKey(subId);
  const current = await getUsage(env, subId);
  const next = current + 1;
  // 40 days = 3,456,000 seconds. Auto-evicts old month buckets.
  await env.QUOTA.put(key, String(next), { expirationTtl: 60 * 60 * 24 * 40 });
  return next;
}

// ---------- AI call: through Gateway if configured, otherwise direct ----------

async function runWorkersAI(
  env: Env,
  model: string,
  messages: ChatMessage[],
): Promise<{ text: string; tokens: number }> {
  // The Workers AI binding (env.AI.run) automatically routes through the
  // account's AI Gateway when one is configured via the binding's gateway option.
  const opts: AiOptions = env.AI_GATEWAY_NAME
    ? { gateway: { id: env.AI_GATEWAY_NAME, skipCache: false, cacheTtl: 3600 } }
    : {};

  const resp = (await env.AI.run(
    model as Parameters<Ai['run']>[0],
    { messages } as never,
    opts,
  )) as { response: string; usage?: { total_tokens?: number } } | { response: string };

  const text = (resp as { response: string }).response ?? '';
  const tokens = (resp as { usage?: { total_tokens?: number } }).usage?.total_tokens ?? 0;
  return { text, tokens };
}

// ---------- Subscriber identification ----------
// MVP: subscriber_id is provided by the client (signed JWT from Substack or magic
// link in future). For now we trust the value if present; otherwise we fall back
// to IP-based anon tracking.

function identifyCaller(req: Request, body: RequestBody): { id: string; isPro: boolean } {
  if (body.subscriber_id && /^[a-zA-Z0-9._@+-]{3,128}$/.test(body.subscriber_id)) {
    return { id: `sub:${body.subscriber_id}`, isPro: true };
  }
  const ip =
    req.headers.get('cf-connecting-ip') ||
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    'unknown';
  return { id: `ip:${ip}`, isPro: false };
}

// ---------- Handlers ----------

async function handleChat(
  req: Request,
  env: Env,
  endpoint: 'reo' | 'tutor',
): Promise<Response> {
  const origin = req.headers.get('origin');
  const cors = corsHeaders(origin, env.ALLOWED_ORIGINS);

  let body: RequestBody;
  try {
    body = (await req.json()) as RequestBody;
  } catch {
    return new Response(JSON.stringify({ error: 'invalid_json' }), {
      status: 400,
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  }

  if (!body.messages || !Array.isArray(body.messages) || body.messages.length === 0) {
    return new Response(JSON.stringify({ error: 'messages_required' }), {
      status: 400,
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  }

  // Clamp to last 12 messages + 1 system to keep token costs predictable.
  const history = body.messages.slice(-12).filter((m) => m.role !== 'system');
  const system: ChatMessage = {
    role: 'system',
    content: endpoint === 'reo' ? REO_SYSTEM : TUTOR_SYSTEM,
  };
  const fullMessages: ChatMessage[] = [system, ...history];

  // Quota check
  const { id, isPro } = identifyCaller(req, body);
  const limit = isPro ? parseInt(env.QUOTA_PRO, 10) : parseInt(env.QUOTA_FREE, 10);
  const used = await getUsage(env, id);

  if (limit > 0 && used >= limit) {
    return new Response(
      JSON.stringify({
        error: 'quota_exhausted',
        message: isPro
          ? `You've used your ${limit} messages this month. To keep going, top up via the upgrade link, or sharpen your own AI toolkit with Perplexity Pro.`
          : `Free tier limit (${limit}/month) reached. Become a Kiwi Dialectic subscriber for ${env.QUOTA_PRO} messages/month — or get Perplexity Pro for your own research stack.`,
        used,
        limit,
        is_pro: isPro,
        upgrade_url: env.UPGRADE_URL,
        perplexity_referral_url: env.PPLX_REFERRAL_URL,
      }),
      {
        status: 402,
        headers: { ...cors, 'Content-Type': 'application/json' },
      },
    );
  }

  // Run the model
  const model = endpoint === 'reo' ? env.REO_MODEL : env.TUTOR_MODEL;
  let result: { text: string; tokens: number };
  try {
    result = await runWorkersAI(env, model, fullMessages);
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: 'model_error',
        detail: err instanceof Error ? err.message : String(err),
      }),
      { status: 502, headers: { ...cors, 'Content-Type': 'application/json' } },
    );
  }

  // Increment quota AFTER a successful response so failed calls don't count.
  const newUsed = await bumpUsage(env, id);

  return new Response(
    JSON.stringify({
      reply: result.text,
      usage: { used: newUsed, limit, is_pro: isPro },
      tokens: result.tokens,
    }),
    {
      status: 200,
      headers: {
        ...cors,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      },
    },
  );
}

// ---------- Worker entrypoint ----------

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const origin = req.headers.get('origin');
    const cors = corsHeaders(origin, env.ALLOWED_ORIGINS);

    // Preflight
    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors });
    }

    // Health
    if (url.pathname === '/' || url.pathname === '/health') {
      return new Response(
        JSON.stringify({
          ok: true,
          service: 'ai-warrior-tutor',
          gateway: env.AI_GATEWAY_NAME || null,
          endpoints: ['/reo', '/tutor'],
        }),
        { status: 200, headers: { ...cors, 'Content-Type': 'application/json' } },
      );
    }

    if (req.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'method_not_allowed' }), {
        status: 405,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    if (url.pathname === '/reo') return handleChat(req, env, 'reo');
    if (url.pathname === '/tutor') return handleChat(req, env, 'tutor');

    return new Response(JSON.stringify({ error: 'not_found' }), {
      status: 404,
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  },
} satisfies ExportedHandler<Env>;
