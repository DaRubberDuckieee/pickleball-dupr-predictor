#!/usr/bin/env python3
"""
Generate mermaid diagrams for trees from Model 3
"""
import pickle
import subprocess

def node_to_mermaid(tree, node_id, parent_id=None, edge_label="", node_counter=[0]):
    """Recursively convert tree nodes to mermaid format"""
    feature = tree.feature[node_id]
    threshold = tree.threshold[node_id]
    
    current_node = f"N{node_counter[0]}"
    node_counter[0] += 1
    
    lines = []
    
    # Check if leaf node
    if feature == -2:  # Leaf node
        value = tree.value[node_id][0][0]
        label = f'Predict: {value:+.3f}'
        
        # Color based on value
        if value > 0.1:
            style = f"style {current_node} fill:#ccffcc"
        elif value < -0.1:
            style = f"style {current_node} fill:#ffcccc"
        elif abs(value) < 0.05:
            style = f"style {current_node} fill:#ffffcc"
        else:
            style = f"style {current_node} fill:#eeffee" if value > 0 else f"style {current_node} fill:#ffeeee"
        
        lines.append(f'    {current_node}["{label}"]')
        lines.append(f'    {style}')
        
        if parent_id:
            lines.insert(0, f'    {parent_id} -->|{edge_label}| {current_node}')
    else:
        # Internal node
        feature_names = ['won', 'rating_diff', 'score_margin', 'total_points', 'partner_diff', 
                        'team_vs_opp', 'won_x_rating_diff', 'won_x_score_margin', 'rating_squared', 
                        'surprise', 'opp_spread', 'player_rating', 'partner_rating', 'opp_avg']
        
        feature_name = feature_names[feature]
        label = f'{feature_name} ≤ {threshold:.2f}?'
        
        lines.append(f'    {current_node}["{label}"]')
        
        if parent_id:
            lines.insert(0, f'    {parent_id} -->|{edge_label}| {current_node}')
        
        # Process children
        left_child = tree.children_left[node_id]
        right_child = tree.children_right[node_id]
        
        lines.extend(node_to_mermaid(tree, left_child, current_node, "Yes", node_counter))
        lines.extend(node_to_mermaid(tree, right_child, current_node, "No", node_counter))
    
    return lines


def tree_to_mermaid(tree, tree_num):
    """Convert a decision tree to mermaid format"""
    mermaid = ["graph TD"]
    lines = node_to_mermaid(tree.tree_, 0, node_counter=[0])
    mermaid.extend(lines)
    return "\n".join(mermaid)


# Load Model 3
print("Loading Model 3...")
with open('models/model3_gb_balanced.pkl', 'rb') as f:
    model, features, deflation = pickle.load(f)

# Generate diagrams for trees 0, 10, 25, 50, 99
tree_indices = [0, 10, 25, 50, 99]

for idx in tree_indices:
    print(f"\nGenerating tree {idx+1}/100...")
    
    tree = model.estimators_[idx, 0]
    mermaid_code = tree_to_mermaid(tree, idx)
    
    # Save mermaid file
    mmd_file = f'tree_visualizations/tree_{idx+1:03d}.mmd'
    with open(mmd_file, 'w') as f:
        f.write(mermaid_code)
    
    # Render with mermaid-cli
    png_file = f'tree_visualizations/tree_{idx+1:03d}.png'
    try:
        result = subprocess.run(
            ['mmdc', '-i', mmd_file, '-o', png_file, '-s', '2', '-w', '1600', '-H', '1200', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"  ✓ Saved {png_file}")
        else:
            print(f"  ✗ Failed to render {png_file}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n✓ Done! Opening folder...")
subprocess.run(['open', 'tree_visualizations/'])
