import re

def format_job_description(text):
    """
    Formats job descriptions without metadata badges.
    """
    if not isinstance(text, str) or not text.strip():
        return "<div class='job-description'><p style='color:#999;'>No job description available.</p></div>"

    text = re.sub(r'\s+', ' ', text.strip())

    # --- Smart section detection ---
    section_keywords = {
        'Job Summary': r'(?:^|\.\s+)(job\s+(?:summary|description|overview)|about\s+(?:the\s+)?(?:role|job|position))[\s:]+',
        'Responsibilities': r'(?:^|\.\s+)(responsibilities|duties|what\s+you\s+(?:will|\'ll)\s+do|key\s+responsibilities|your\s+role)[\s:]+',
        'Requirements': r'(?:^|\.\s+)(requirements|qualifications|required\s+qualifications|what\s+we\s+need|minimum\s+qualifications|must\s+have)[\s:]+',
        'Skills': r'(?:^|\.\s+)(required\s+skills|technical\s+skills|key\s+skills|skills\s+required)[\s:]+',
        'Preferred': r'(?:^|\.\s+)(preferred\s+qualifications?|nice\s+to\s+have|bonus\s+points?|good\s+to\s+have|desired)[\s:]+',
        'Benefits': r'(?:^|\.\s+)(benefits|what\s+we\s+offer|perks|why\s+join)[\s:]+',
        'Education': r'(?:^|\.\s+)(education|degree|academic\s+qualifications?)[\s:]+',
    }

    # Find section headers
    section_positions = []
    for display_name, pattern in section_keywords.items():
        for match in re.finditer(pattern, text, re.I):
            section_positions.append({
                'name': display_name,
                'start': match.start(),
                'end': match.end(),
                'matched_text': match.group(1)
            })

    # Sort and deduplicate
    section_positions.sort(key=lambda x: x['start'])
    seen_sections = set()
    unique_sections = []

    for sec in section_positions:
        if sec['name'] not in seen_sections:
            seen_sections.add(sec['name'])
            unique_sections.append(sec)

    section_positions = unique_sections

    # --- Parse content ---
    formatted_parts = []

    if not section_positions:
        # No clear sections - treat entire text as description
        items = smart_split(text)

        if items:
            formatted_parts.append("<h4 class='section-title'>Job Description</h4>")
            for item in items:
                formatted_parts.append(
                    f"<div class='job-bullet'><span class='job-bullet-dot'>•</span>{item}</div>"
                )
    else:
        # Process each detected section
        for i, section in enumerate(section_positions):
            start = section['end']
            end = section_positions[i + 1]['start'] if i + 1 < len(section_positions) else len(text)
            content = text[start:end].strip()

            content = re.sub(r'^' + re.escape(section['matched_text']) + r'[\s:]*', '', content, flags=re.I)

            if len(content) < 15:
                continue

            formatted_parts.append(f"<h4 class='section-title'>{section['name']}</h4>")

            items = smart_split(content)
            if not items:
                if len(content) > 20:
                    formatted_parts.append(f"<p style='margin-bottom:1em; line-height:1.7;'>{content}</p>")
                continue

            for item in items:
                formatted_parts.append(
                    f"<div class='job-bullet'><span class='job-bullet-dot'>•</span>{item}</div>"
                )

    # --- Final HTML ---
    result = "<div class='job-description' style='color:#dddddd; font-size:1em;'>"

    if formatted_parts:
        result += ''.join(formatted_parts)
    else:
        result += "<p style='color:#999;'>No detailed description available.</p>"

    result += "</div>"
    return result


def smart_split(text):
    text = text.strip()
    items = re.split(r'\.\s+(?=[A-Z0-9])', text)
    if not text.endswith('.'):
        last = text.split('.')[-1].strip()
        if last and last not in items[-1]:
            items.append(last)
    clean_items = []
    for item in items:
        s = item.strip()
        if not s:
            continue
        if not s.endswith('.'):
            s += '.'
        clean_items.append(s)
    return clean_items
