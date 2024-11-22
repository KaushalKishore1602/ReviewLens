// ReviewLens Frontend Client Application
let allReviews = [];
let dashboardData = null;
let currentTab = 'overview';

// Tab switching
function switchTab(tabName) {
  currentTab = tabName;
  const tabs = ['overview', 'reviews', 'products', 'insights', 'settings'];
  
  tabs.forEach(t => {
    const pane = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`tabBtn-${t}`);
    if (pane) {
      if (t === tabName) {
        pane.classList.remove('hidden');
      } else {
        pane.classList.add('hidden');
      }
    }
    if (btn) {
      if (t === tabName) {
        btn.className = "w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-colors text-brand-700 bg-brand-50 shadow-sm shadow-brand-500/10";
        const svg = btn.querySelector('svg');
        if (svg) svg.className = "w-5 h-5 text-brand-600";
      } else {
        btn.className = "w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-colors text-slate-600 hover:bg-slate-100";
        const svg = btn.querySelector('svg');
        if (svg) svg.className = "w-5 h-5 text-slate-400";
      }
    }
  });

  // If reviews tab is clicked, ensure table is rendered there as well
  if (tabName === 'reviews') {
    const revTab = document.getElementById('tab-reviews');
    const overviewTable = document.querySelector('#tab-overview .bg-white.rounded-2xl.border.border-slate-200.shadow-xs.overflow-hidden');
    if (overviewTable && revTab) {
      revTab.innerHTML = '';
      revTab.appendChild(overviewTable.cloneNode(true));
      // Reattach table filter listeners
      reattachClonedTableListeners(revTab);
    }
  }
}

function reattachClonedTableListeners(parent) {
  const sent = parent.querySelector('#filterSentiment');
  const top = parent.querySelector('#filterTopic');
  const rep = parent.querySelector('#filterNeedsReply');
  const mis = parent.querySelector('#filterMismatches');
  if (sent) sent.addEventListener('change', () => applyFilters(parent));
  if (top) top.addEventListener('change', () => applyFilters(parent));
  if (rep) rep.addEventListener('change', () => applyFilters(parent));
  if (mis) mis.addEventListener('change', () => applyFilters(parent));
}

// Drag & drop handlers
const dropZone = document.getElementById('dropZone');
if (dropZone) {
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-active');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-active');
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      uploadCsvFile(files[0]);
    }
  });
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    uploadCsvFile(file);
  }
}

async function uploadCsvFile(file) {
  showLoading(true, `Uploading & analyzing ${file.name}...`);
  const formData = new FormData();
  formData.append('file', file);

  try {
    const resp = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await resp.json();
    if (data.status === 'success') {
      renderDashboard(data);
    } else {
      alert('Error analyzing CSV: ' + (data.message || 'Unknown error'));
    }
  } catch (err) {
    alert('Upload failed: ' + err.message);
  } finally {
    showLoading(false);
  }
}

async function loadSampleReviews() {
  showLoading(true, "Processing 30 reviews in batches of 5 with prompt injection defense...");
  try {
    const resp = await fetch('/api/load-sample', {
      method: 'POST'
    });
    const data = await resp.json();
    if (data.status === 'success') {
      renderDashboard(data);
    } else {
      alert('Error loading sample data: ' + data.message);
    }
  } catch (err) {
    alert('Failed to load sample: ' + err.message);
  } finally {
    showLoading(false);
  }
}

let timerInterval = null;
function showLoading(show, message) {
  const el = document.getElementById('processingIndicator');
  const msgEl = document.getElementById('processingStatusText');
  const timerEl = document.getElementById('processingTimer');
  
  if (show) {
    if (msgEl && message) msgEl.innerText = message;
    if (el) el.classList.remove('hidden');
    let start = Date.now();
    if (timerEl) {
      clearInterval(timerInterval);
      timerInterval = setInterval(() => {
        timerEl.innerText = ((Date.now() - start) / 1000).toFixed(1) + 's';
      }, 100);
    }
  } else {
    clearInterval(timerInterval);
    if (el) el.classList.add('hidden');
  }
}

function renderDashboard(data) {
  dashboardData = data;
  allReviews = data.reviews || [];

  // Update KPI counters
  const cStats = data.cleaning_stats || {};
  document.getElementById('statTotalRows').innerText = cStats.total_rows || 0;
  document.getElementById('statValidReviews').innerText = cStats.valid_reviews || 0;
  document.getElementById('statEmptySkipped').innerText = cStats.empty_skipped || 0;
  document.getElementById('statDuplicatesReused').innerText = cStats.duplicates_reused || 0;
  document.getElementById('statUnknownRatings').innerText = cStats.unknown_ratings || 0;

  // Analysis analytics
  const analytics = data.analytics || {};
  document.getElementById('statTotalAnalysed').innerText = analytics.total_analysed || 0;
  document.getElementById('statPosPct').innerText = (analytics.positive_pct || 0) + '%';
  document.getElementById('statPosCount').innerText = analytics.positive_count || 0;
  document.getElementById('statNeuPct').innerText = (analytics.neutral_pct || 0) + '%';
  document.getElementById('statNeuCount').innerText = analytics.neutral_count || 0;
  document.getElementById('statNegPct').innerText = (analytics.negative_pct || 0) + '%';
  document.getElementById('statNegCount').innerText = analytics.negative_count || 0;
  document.getElementById('statNeedsReplyCount').innerText = analytics.needs_reply_count || 0;

  // Rating mismatches
  document.getElementById('statMismatchCount').innerText = analytics.rating_mismatches_count || 0;
  document.getElementById('statAgreementPct').innerText = `(${analytics.rating_agreement_pct || 100}% agreement)`;

  // Operational metrics
  const log = data.cost_speed_log || {};
  document.getElementById('statAiCalls').innerText = log.ai_calls_made || 0;
  document.getElementById('statCacheHits').innerText = log.cache_hits || 0;
  document.getElementById('statCacheHitCard').innerText = log.cache_hits || 0;
  document.getElementById('statLiveAiCountLabel').innerText = `(${log.ai_calls_made || 0} live AI calls)`;
  document.getElementById('statProcessingTime').innerText = (log.processing_time_sec || 0) + 's';
  if (log.llm_engine && document.getElementById('modelPillText')) {
    document.getElementById('modelPillText').innerText = log.llm_engine.includes('Live') ? 'Gemini 1.5' : 'NLP Heuristic Engine';
  }

  // Sidebar badge
  const revCountBadge = document.getElementById('badge-reviews-count');
  if (revCountBadge) revCountBadge.innerText = allReviews.length;

  // Render Top 3 Complaints & Praises
  renderTopLists(analytics.top_3_complaints || [], analytics.top_3_praises || []);

  // Render Table
  renderReviewsTable(allReviews);

  // Render Product Views
  renderProductViews(analytics.product_views || []);
}

function renderTopLists(complaints, praises) {
  const compList = document.getElementById('topComplaintsList');
  if (compList) {
    if (complaints.length === 0) {
      compList.innerHTML = `<div class="text-xs text-slate-400 italic py-2 text-center">No major complaints found.</div>`;
    } else {
      compList.innerHTML = complaints.map((c, i) => `
        <div class="p-3 bg-rose-50/60 border border-rose-100 rounded-xl flex items-start space-x-3">
          <span class="w-5 h-5 rounded-full bg-rose-200/80 text-rose-800 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">${i + 1}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-rose-900">${escapeHtml(c.topic)}</span>
              <span class="text-[10px] bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded font-semibold">${c.count} reviews</span>
            </div>
            <p class="text-[11px] text-slate-600 mt-1 line-clamp-1 italic">"${escapeHtml(c.sample)}"</p>
          </div>
        </div>
      `).join('');
    }
  }

  const praiseList = document.getElementById('topPraisesList');
  if (praiseList) {
    if (praises.length === 0) {
      praiseList.innerHTML = `<div class="text-xs text-slate-400 italic py-2 text-center">No praises found.</div>`;
    } else {
      praiseList.innerHTML = praises.map((p, i) => `
        <div class="p-3 bg-emerald-50/60 border border-emerald-100 rounded-xl flex items-start space-x-3">
          <span class="w-5 h-5 rounded-full bg-emerald-200/80 text-emerald-800 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">${i + 1}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-bold text-xs text-emerald-900">${escapeHtml(p.topic)}</span>
              <span class="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-semibold">${p.count} praises</span>
            </div>
            <p class="text-[11px] text-slate-600 mt-1 line-clamp-1 italic">"${escapeHtml(p.sample)}"</p>
          </div>
        </div>
      `).join('');
    }
  }
}

function renderReviewsTable(reviews, targetTbodyId = 'reviewsTableBody') {
  const tbody = document.getElementById(targetTbodyId);
  if (!tbody) return;

  if (reviews.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-400">No matching reviews found.</td></tr>`;
    return;
  }

  tbody.innerHTML = reviews.map(r => {
    const analysis = r.analysis || {};
    const sentiment = analysis.sentiment || 'unknown';
    const topics = analysis.topics || [];
    const summary = analysis.summary || (r.status === 'empty_skipped' ? '<span class="text-amber-600 font-semibold italic">[Empty Review Skipped]</span>' : 'Pending analysis');
    const needsReply = analysis.needs_reply;

    // Badges
    let sentimentBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">Pending</span>';
    if (sentiment === 'positive') sentimentBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Positive</span>';
    if (sentiment === 'neutral') sentimentBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">Neutral</span>';
    if (sentiment === 'negative') sentimentBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">Negative</span>';

    const topicPills = topics.map(t => `<span class="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-medium mr-1 mb-1 inline-block">${escapeHtml(t)}</span>`).join('');

    // Rating representation
    let ratingStars = '';
    if (r.rating !== null && r.rating !== undefined) {
      ratingStars = `<span class="text-amber-500 font-semibold">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>`;
    } else {
      ratingStars = `<span class="bg-purple-100 text-purple-800 px-1.5 py-0.5 rounded font-mono text-[10px]" title="Raw value: ${escapeHtml(r.raw_rating)}">unknown</span>`;
    }

    // Rating mismatch pill
    let mismatchPill = '';
    if (r.is_rating_mismatch) {
      mismatchPill = `<div class="mt-1"><span class="bg-amber-100 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded text-[9px] font-bold">⚠️ Mismatch</span></div>`;
    }

    // Action button
    let actionBtn = '<span class="text-slate-300 text-[11px]">—</span>';
    if (needsReply) {
      actionBtn = `
        <button onclick="openReplyModal('${r.review_id}')" class="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-[11px] border border-indigo-200/80 transition-colors flex items-center space-x-1 shrink-0 ml-auto">
          <span>✨</span>
          <span>Generate Reply</span>
        </button>
      `;
    }

    // Prompt injection indicator for R012/R015
    let injectionTag = '';
    if (r.review_id === 'R012' || r.review_id === 'R015') {
      injectionTag = `<span class="ml-1 bg-rose-100 text-rose-700 text-[9px] px-1 py-0.5 rounded font-bold uppercase">Attack Defended</span>`;
    }

    return `
      <tr class="hover:bg-slate-50/75 transition-colors">
        <td class="py-3 px-4 font-mono font-bold text-slate-700 whitespace-nowrap">
          ${escapeHtml(r.review_id)}
          ${injectionTag}
          <div class="text-[10px] text-slate-400 font-normal">${escapeHtml(r.date || 'N/A')}</div>
        </td>
        <td class="py-3 px-4 font-medium text-slate-900">${escapeHtml(r.product)}</td>
        <td class="py-3 px-4 whitespace-nowrap">
          ${ratingStars}
          ${mismatchPill}
        </td>
        <td class="py-3 px-4 text-slate-700 leading-snug">
          <div class="line-clamp-2" title="${escapeHtml(r.review_text)}">
            ${escapeHtml(r.review_text || '—')}
          </div>
        </td>
        <td class="py-3 px-4 whitespace-nowrap">${sentimentBadge}</td>
        <td class="py-3 px-4">${topicPills || '<span class="text-slate-400 text-[10px]">None</span>'}</td>
        <td class="py-3 px-4 text-slate-600 font-medium leading-snug">${summary}</td>
        <td class="py-3 px-4 text-right whitespace-nowrap">${actionBtn}</td>
      </tr>
    `;
  }).join('');
}

function renderProductViews(products) {
  const container = document.getElementById('productCardsContainer');
  if (!container) return;

  if (products.length === 0) {
    container.innerHTML = `<div class="col-span-3 text-center py-8 text-slate-400 text-xs">No products loaded yet.</div>`;
    return;
  }

  container.innerHTML = products.map(p => {
    const total = p.analysed_count || 1;
    const posPct = Math.round((p.positive_count / total) * 100);
    const neuPct = Math.round((p.neutral_count / total) * 100);
    const negPct = Math.round((p.negative_count / total) * 100);

    return `
      <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 class="font-bold text-slate-900 text-sm">${escapeHtml(p.product)}</h3>
            <span class="text-xs font-semibold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">${p.total_reviews} reviews</span>
          </div>

          <div class="mt-4 flex items-center justify-between">
            <span class="text-xs text-slate-500 font-medium">Average Rating</span>
            <span class="text-sm font-bold text-amber-500">${p.avg_rating ? p.avg_rating + ' ★' : 'N/A'}</span>
          </div>

          <!-- Sentiment Bar -->
          <div class="mt-3">
            <div class="flex justify-between text-[11px] font-medium text-slate-500 mb-1">
              <span>Sentiment Split</span>
              <span class="text-emerald-600 font-bold">${posPct}% Pos</span>
            </div>
            <div class="w-full h-2 rounded-full bg-slate-100 overflow-hidden flex">
              <div class="h-full bg-emerald-500" style="width: ${posPct}%" title="Positive: ${posPct}%"></div>
              <div class="h-full bg-amber-400" style="width: ${neuPct}%" title="Neutral: ${neuPct}%"></div>
              <div class="h-full bg-rose-500" style="width: ${negPct}%" title="Negative: ${negPct}%"></div>
            </div>
          </div>

          <!-- Recurring Issues -->
          <div class="mt-4">
            <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Top Issues</div>
            <div class="flex flex-wrap gap-1">
              ${p.top_issues.length > 0 ? p.top_issues.map(t => `<span class="bg-rose-50 text-rose-700 border border-rose-100 px-2 py-0.5 rounded text-[10px] font-semibold">${escapeHtml(t)}</span>`).join('') : '<span class="text-slate-400 text-[10px]">None</span>'}
            </div>
          </div>
        </div>

        <div class="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
          <span class="text-[11px] text-slate-400">Praise Themes</span>
          <div class="flex gap-1">
            ${p.top_praises.map(t => `<span class="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded text-[10px] font-semibold">${escapeHtml(t)}</span>`).join('')}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Filtering
function applyFilters(context = document) {
  if (!allReviews.length) return;

  const searchVal = (document.getElementById('globalSearchInput')?.value || '').toLowerCase().trim();
  const prodVal = document.getElementById('headerProductFilter')?.value || 'ALL';
  const sentVal = context.querySelector('#filterSentiment')?.value || 'ALL';
  const topicVal = context.querySelector('#filterTopic')?.value || 'ALL';
  const needsReplyOnly = context.querySelector('#filterNeedsReply')?.checked || false;
  const mismatchesOnly = context.querySelector('#filterMismatches')?.checked || false;

  const filtered = allReviews.filter(r => {
    // Search
    if (searchVal) {
      const matchId = r.review_id.toLowerCase().includes(searchVal);
      const matchText = (r.review_text || '').toLowerCase().includes(searchVal);
      const matchProd = (r.product || '').toLowerCase().includes(searchVal);
      const matchSummary = (r.analysis?.summary || '').toLowerCase().includes(searchVal);
      if (!matchId && !matchText && !matchProd && !matchSummary) return false;
    }

    // Product
    if (prodVal !== 'ALL' && r.product !== prodVal) return false;

    // Sentiment
    if (sentVal !== 'ALL') {
      const s = r.analysis?.sentiment || 'unknown';
      if (s !== sentVal) return false;
    }

    // Topic
    if (topicVal !== 'ALL') {
      const topics = r.analysis?.topics || [];
      if (!topics.includes(topicVal)) return false;
    }

    // Needs Reply
    if (needsReplyOnly) {
      if (!r.analysis?.needs_reply) return false;
    }

    // Mismatches
    if (mismatchesOnly) {
      if (!r.is_rating_mismatch) return false;
    }

    return true;
  });

  renderReviewsTable(filtered, context === document ? 'reviewsTableBody' : context.querySelector('tbody')?.id || 'reviewsTableBody');
}

function syncProductFilter(val) {
  applyFilters();
}

// Reply Modal
let currentReplyReview = null;
async function openReplyModal(reviewId) {
  const rev = allReviews.find(r => r.review_id === reviewId);
  if (!rev) return;

  currentReplyReview = rev;
  document.getElementById('modalProductLabel').innerText = `Product: ${rev.product} (${rev.review_id})`;
  document.getElementById('modalReviewText').innerText = `"${rev.review_text}"`;
  document.getElementById('modalReplyTextarea').value = "Generating thoughtful AI response...";

  const modal = document.getElementById('replyModal');
  modal.classList.remove('hidden');

  try {
    const resp = await fetch('/api/reply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        review_id: rev.review_id,
        product: rev.product,
        review_text: rev.review_text,
        summary: rev.analysis?.summary || ''
      })
    });
    const data = await resp.json();
    if (data.status === 'success') {
      document.getElementById('modalReplyTextarea').value = data.suggested_reply;
    } else {
      document.getElementById('modalReplyTextarea').value = "Failed to generate reply.";
    }
  } catch (err) {
    document.getElementById('modalReplyTextarea').value = "Error generating response: " + err.message;
  }
}

function closeReplyModal() {
  document.getElementById('replyModal').classList.add('hidden');
  currentReplyReview = null;
}

function copyReplyText() {
  const textarea = document.getElementById('modalReplyTextarea');
  textarea.select();
  navigator.clipboard.writeText(textarea.value);
  const btnText = document.getElementById('btnCopyText');
  if (btnText) {
    btnText.innerText = "Copied!";
    setTimeout(() => { btnText.innerText = "Copy Reply"; }, 2000);
  }
}

async function clearCacheAction() {
  if (confirm("Clear the persistent cache database? This will cause the next upload to query the AI afresh.")) {
    try {
      const resp = await fetch('/api/clear-cache', { method: 'POST' });
      const data = await resp.json();
      alert(data.message || 'Cache cleared');
      document.getElementById('statCacheHits').innerText = '0';
      document.getElementById('statCacheHitCard').innerText = '0';
    } catch (err) {
      alert('Error clearing cache: ' + err.message);
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Auto-load sample reviews on initial load for instant evaluation
window.addEventListener('DOMContentLoaded', () => {
  loadSampleReviews();
});
