def _normalize_llm_content(content):
    cleaned = str(content).strip()
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE).strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned.strip()


def _parse_llm_batch(content, expected_source_indices):
    cleaned = _normalize_llm_content(content)
    expected_source_indices = {int(idx) for idx in expected_source_indices}
    candidates = [cleaned]

    object_match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
    if object_match:
        candidates.append(object_match.group(0))

    array_match = re.search(r'\[.*\]', cleaned, flags=re.DOTALL)
    if array_match:
        candidates.append(array_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            items = parsed.get('results')
        elif isinstance(parsed, list):
            items = parsed
        else:
            items = None

        if not isinstance(items, list):
            continue

        parsed_results = {}
        for item in items:
            if not isinstance(item, dict):
                continue

            try:
                source_index = int(item.get('source_index'))
                label = int(item.get('label'))
                confidence = float(item.get('confidence'))
            except (TypeError, ValueError):
                continue

            if source_index in expected_source_indices and label in {0, 1} and 0.0 <= confidence <= 1.0:
                parsed_results[source_index] = (label, round(confidence, 4))

        if parsed_results:
            return parsed_results

    line_pattern = re.compile(
        r'(?im)^\s*source_index\s*[=:]\s*(\d+)\s*\|\s*label\s*[=:]\s*([01])\s*\|\s*confidence\s*[=:]\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$'
    )
    line_results = {}
    for match in line_pattern.finditer(cleaned):
        source_index = int(match.group(1))
        label = int(match.group(2))
        confidence = float(match.group(3))
        if source_index in expected_source_indices:
            line_results[source_index] = (label, round(confidence, 4))
    if line_results:
        return line_results

    block_pattern = re.compile(r'(?ims)^\s*source_index\s*:\s*(\d+)(.*?)(?=^\s*source_index\s*:\s*\d+|\Z)')
    label_pattern = re.compile(
        r'label\s*[=:]\s*([01]).*?confidence\s*[=:]\s*(0(?:\.\d+)?|1(?:\.0+)?)',
        flags=re.IGNORECASE | re.DOTALL,
    )
    block_results = {}
    for match in block_pattern.finditer(cleaned):
        source_index = int(match.group(1))
        body = match.group(2)
        label_match = label_pattern.search(body)
        if source_index in expected_source_indices and label_match:
            block_results[source_index] = (int(label_match.group(1)), round(float(label_match.group(2)), 4))
    if block_results:
        return block_results

    raise ValueError(f'Could not parse valid batch results from response: {content[:300]}')


def _description_hash(text):
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


def _prepare_job_description_excerpt(text, max_chars=LM_JOB_DESCRIPTION_CHAR_LIMIT):
    normalized = re.sub(r'\s+', ' ', str(text)).strip()
    if len(normalized) <= max_chars:
        return normalized

    lower_normalized = normalized.lower()
    focus_terms = ['machine learning', 'ml ', ' ai/ml', 'artificial intelligence']
    focus_index = -1
    for term in focus_terms:
        focus_index = lower_normalized.find(term)
        if focus_index != -1:
            break

    if focus_index == -1:
        excerpt = normalized[:max_chars]
        return excerpt + (' ...' if len(normalized) > max_chars else '')

    start = max(0, focus_index - max_chars // 3)
    end = min(len(normalized), start + max_chars)
    start = max(0, end - max_chars)
    excerpt = normalized[start:end]

    if start > 0:
        excerpt = '... ' + excerpt
    if end < len(normalized):
        excerpt = excerpt + ' ...'
    return excerpt


def _cache_rows_from_lookup(cache_lookup):
    rows = []
    for (source_index, description_hash, model_id), (label, confidence) in cache_lookup.items():
        rows.append({
            'source_index': int(source_index),
            'description_hash': description_hash,
            'llm_ml_label': int(label),
            'llm_ml_confidence': float(confidence),
            'model_id': model_id,
        })
    return rows


def _save_llm_cache(cache_lookup):
    cache_df = pd.DataFrame(_cache_rows_from_lookup(cache_lookup), columns=LM_CACHE_COLUMNS)
    if not cache_df.empty:
        cache_df = cache_df.sort_values(['source_index', 'description_hash', 'model_id'])
        cache_df = cache_df.drop_duplicates(['source_index', 'description_hash', 'model_id'], keep='last')
    cache_df.to_csv(LM_CACHE_PATH, index=False)


def _build_batch_payload(batch_frame):
    blocks = []
    for source_index, row in batch_frame.iterrows():
        job_title = str(row.get('job_title', ''))
        job_description_excerpt = _prepare_job_description_excerpt(row['job_description_skills'])
        block = (
            f"source_index: {int(source_index)}\n"
            f"job_title: {job_title}\n"
            f"job_description_excerpt:\n{job_description_excerpt}"
        )
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


def _classify_ml_relevance_batch(batch_frame, max_retries=3):
    expected_source_indices = [int(idx) for idx in batch_frame.index]
    batch_payload = _build_batch_payload(batch_frame)
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            payload = {
                'model': LM_STUDIO_MODEL,
                'messages': [
                    {'role': 'system', 'content': 'Return one compact classification per source_index.'},
                    {'role': 'user', 'content': LM_ML_PROMPT_TEMPLATE.format(batch_payload=batch_payload)},
                ],
                'temperature': LM_TEMPERATURE,
                'max_tokens': 5000 + (attempt - 1) * 1500,
            }

            response = request.urlopen(
                request.Request(
                    f'{LM_STUDIO_BASE_URL}/chat/completions',
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST',
                ),
                timeout=LM_TIMEOUT_SECONDS,
            )
            response_json = json.loads(response.read().decode('utf-8'))
            message = response_json['choices'][0]['message']
            content = (message.get('content') or '').strip()
            reasoning_content = (message.get('reasoning_content') or '').strip()
            parse_target = content or reasoning_content
            return _parse_llm_batch(parse_target, expected_source_indices)
        except (error.URLError, error.HTTPError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(min(2 * attempt, 5))
            else:
                raise RuntimeError(f'LLM batch classification failed after {max_retries} attempts: {exc}') from exc

    raise RuntimeError(f'LLM batch classification failed: {last_error}')
