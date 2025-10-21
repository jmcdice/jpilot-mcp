"""Parser for Atlassian Document Format (ADF) to plain text.

Jira Cloud uses ADF for rich text fields like descriptions and comments.
This module converts ADF JSON structures to readable plain text.
"""

from typing import Any


def _property_holder_to_dict(obj: Any) -> Any:
    """Convert a PropertyHolder object to a dictionary recursively.

    Args:
        obj: PropertyHolder object or other value

    Returns:
        Dictionary representation or original value
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, dict):
        # Already a dict, but recursively convert values
        return {k: _property_holder_to_dict(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        # It's a list or tuple
        return [_property_holder_to_dict(item) for item in obj]

    if hasattr(obj, '__dict__'):
        # It's an object with attributes (like PropertyHolder)
        result = {}
        for attr in dir(obj):
            if not attr.startswith('_') and not callable(getattr(obj, attr, None)):
                try:
                    value = getattr(obj, attr)
                    result[attr] = _property_holder_to_dict(value)
                except:
                    pass
        return result

    return obj


def adf_to_text(adf: Any) -> str:
    """Convert Atlassian Document Format to plain text.

    Args:
        adf: ADF content (can be string, dict, or PropertyHolder object)

    Returns:
        Plain text representation of the content
    """
    # Handle None
    if adf is None:
        return ""

    # If it's already a string, return it
    if isinstance(adf, str):
        return adf

    # Convert PropertyHolder objects to dict first
    if not isinstance(adf, dict):
        adf = _property_holder_to_dict(adf)

    # If it's still not a dict at this point, convert to string
    if not isinstance(adf, dict):
        return str(adf)

    # Parse ADF structure
    return _parse_adf_node(adf)


def _parse_adf_node(node: dict) -> str:
    """Recursively parse an ADF node to extract text.
    
    Args:
        node: ADF node dictionary
        
    Returns:
        Plain text from this node and its children
    """
    if not isinstance(node, dict):
        return str(node)
    
    node_type = node.get('type', '')
    content = node.get('content', [])
    text = node.get('text', '')
    
    # Handle different node types
    if node_type == 'text':
        # Plain text node
        result = text
        
        # Apply marks (bold, italic, etc.)
        marks = node.get('marks', [])
        for mark in marks:
            mark_type = mark.get('type', '')
            if mark_type == 'code':
                result = f'`{result}`'
            elif mark_type == 'strong':
                result = f'**{result}**'
            elif mark_type == 'em':
                result = f'*{result}*'
            elif mark_type == 'strike':
                result = f'~~{result}~~'
            elif mark_type == 'link':
                href = mark.get('attrs', {}).get('href', '')
                if href:
                    result = f'{result} ({href})'
        
        return result
    
    elif node_type == 'paragraph':
        # Paragraph - join content and add newline
        parts = [_parse_adf_node(child) for child in content]
        return ''.join(parts) + '\n\n'
    
    elif node_type == 'heading':
        # Heading - add appropriate prefix
        level = node.get('attrs', {}).get('level', 1)
        parts = [_parse_adf_node(child) for child in content]
        heading_text = ''.join(parts)
        return f"{'#' * level} {heading_text}\n\n"
    
    elif node_type == 'bulletList':
        # Bullet list
        items = [_parse_adf_node(child) for child in content]
        return ''.join(items)
    
    elif node_type == 'orderedList':
        # Ordered list
        items = []
        for i, child in enumerate(content, 1):
            item_text = _parse_adf_node(child)
            # Remove trailing newlines from item
            item_text = item_text.rstrip('\n')
            items.append(f"{i}. {item_text}\n")
        return ''.join(items) + '\n'
    
    elif node_type == 'listItem':
        # List item
        parts = [_parse_adf_node(child) for child in content]
        item_text = ''.join(parts).rstrip('\n')
        return f"• {item_text}\n"
    
    elif node_type == 'codeBlock':
        # Code block
        parts = [_parse_adf_node(child) for child in content]
        code = ''.join(parts).rstrip('\n')
        language = node.get('attrs', {}).get('language', '')
        return f"```{language}\n{code}\n```\n\n"
    
    elif node_type == 'blockquote':
        # Blockquote
        parts = [_parse_adf_node(child) for child in content]
        quote = ''.join(parts).rstrip('\n')
        # Prefix each line with >
        lines = quote.split('\n')
        quoted = '\n'.join(f"> {line}" for line in lines)
        return f"{quoted}\n\n"
    
    elif node_type == 'rule':
        # Horizontal rule
        return "---\n\n"
    
    elif node_type == 'hardBreak':
        # Line break
        return '\n'
    
    elif node_type == 'mention':
        # User mention
        mention_text = node.get('attrs', {}).get('text', '@user')
        return mention_text
    
    elif node_type == 'emoji':
        # Emoji
        shortName = node.get('attrs', {}).get('shortName', '')
        return shortName or '😀'
    
    elif node_type == 'inlineCard' or node_type == 'blockCard':
        # Link card
        url = node.get('attrs', {}).get('url', '')
        return f"[Link: {url}]\n\n" if url else ""
    
    elif node_type == 'mediaGroup' or node_type == 'mediaSingle':
        # Media (images, etc.)
        return "[Image]\n\n"
    
    elif node_type == 'table':
        # Table - simplified representation
        rows = [_parse_adf_node(child) for child in content]
        return ''.join(rows) + '\n'
    
    elif node_type == 'tableRow':
        # Table row
        cells = [_parse_adf_node(child) for child in content]
        return '| ' + ' | '.join(cell.strip() for cell in cells) + ' |\n'
    
    elif node_type == 'tableHeader' or node_type == 'tableCell':
        # Table cell
        parts = [_parse_adf_node(child) for child in content]
        return ''.join(parts)
    
    elif node_type == 'panel':
        # Panel (info, warning, etc.)
        panel_type = node.get('attrs', {}).get('panelType', 'info')
        parts = [_parse_adf_node(child) for child in content]
        panel_text = ''.join(parts).rstrip('\n')
        return f"[{panel_type.upper()}]\n{panel_text}\n\n"
    
    elif node_type == 'doc':
        # Document root - just process content
        parts = [_parse_adf_node(child) for child in content]
        return ''.join(parts).strip()
    
    else:
        # Unknown node type - try to process content
        if content:
            parts = [_parse_adf_node(child) for child in content]
            return ''.join(parts)
        elif text:
            return text
        else:
            return ""


def extract_text_from_jira_field(field: Any) -> str:
    """Extract plain text from a Jira field that might contain ADF.
    
    This is a convenience wrapper around adf_to_text that handles
    common Jira field formats.
    
    Args:
        field: Jira field value (description, comment body, etc.)
        
    Returns:
        Plain text representation
    """
    return adf_to_text(field)

