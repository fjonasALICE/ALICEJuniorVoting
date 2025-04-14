import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import textwrap
from collections import Counter

def read_survey_data(file_path):
    """Read survey data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        sys.exit(1)

def analyze_question(df, question_column):
    """
    Analyze a specific question from the survey data.
    Returns the count and percentage for each answer, excluding 'NO OPINION' responses.
    Also returns the count of 'NO OPINION' responses.
    """
    # Count total number of rows (all responses)
    total_rows = len(df)
    
    # Get all responses for this question
    all_responses = df[question_column].dropna()
    
    # Filter out "NO OPINION" responses
    no_opinion_pattern = "NO OPINION"
    no_opinion_mask = all_responses.str.contains(no_opinion_pattern, case=False, na=False)
    no_opinion_count = no_opinion_mask.sum()
    
    # Get valid responses (excluding NO OPINION)
    responses = all_responses[~no_opinion_mask]
    
    # Count occurrences of each response
    response_counts = Counter(responses)
    
    # Calculate total valid responses (excluding NO OPINION)
    total_valid_responses = len(responses)
    
    if total_valid_responses == 0:
        return {}, {}, 0, no_opinion_count
    
    # Calculate percentages
    response_percentages = {answer: (count / total_valid_responses) * 100 
                           for answer, count in response_counts.items()}
    
    return response_counts, response_percentages, total_valid_responses, no_opinion_count

def allocate_three_votes(percentages):
    """
    Allocate 3 votes based on the percentages of each answer.
    Uses the largest remainder method.
    Returns the vote allocation and step-by-step calculation details.
    """
    if not percentages:
        return {}, ""
    
    # For storing the step-by-step calculation for display
    calculation_steps = []
    
    # Initial allocation based on percentages
    votes_per_answer = {}
    remaining = {}
    
    # Step 1: Calculate initial quotas
    calculation_steps.append("Step 1: Calculate proportional votes (percentage × 3)")
    for answer, pct in percentages.items():
        # Calculate votes proportionally (out of 3)
        votes = (pct / 100) * 3
        # Format for display
        calculation_steps.append(f"  {answer}: {pct:.1f}% × 3 = {votes:.2f}")
    
    # Step 2: Allocate whole votes
    calculation_steps.append("\nStep 2: Allocate whole votes only")
    for answer, pct in percentages.items():
        votes = (pct / 100) * 3
        # Whole votes
        whole_votes = int(votes)
        votes_per_answer[answer] = whole_votes
        # Remainder for potential additional votes
        remaining[answer] = votes - whole_votes
        calculation_steps.append(f"  {answer}: {whole_votes} vote(s) (remainder: {remaining[answer]:.2f})")
    
    # Allocate remaining votes based on largest remainder
    votes_allocated = sum(votes_per_answer.values())
    votes_remaining = 3 - votes_allocated
    
    # Step 3: Sort by remainder
    calculation_steps.append(f"\nStep 3: Allocate {votes_remaining} remaining vote(s) by largest remainder")
    
    # Sort answers by remainder in descending order
    sorted_answers = sorted(remaining.items(), key=lambda x: x[1], reverse=True)
    
    # Show remainders in descending order
    for i, (answer, remainder) in enumerate(sorted_answers):
        if i < votes_remaining:
            calculation_steps.append(f"  {answer}: +1 vote (remainder: {remainder:.2f})")
        else:
            calculation_steps.append(f"  {answer}: +0 votes (remainder: {remainder:.2f})")
    
    # Step 4: Allocate remaining votes
    for i in range(votes_remaining):
        if i < len(sorted_answers):
            answer = sorted_answers[i][0]
            votes_per_answer[answer] += 1
    
    # Step 5: Final allocation
    calculation_steps.append("\nFinal 3-vote allocation:")
    for answer, votes in sorted(votes_per_answer.items(), key=lambda x: x[1], reverse=True):
        if votes > 0:
            calculation_steps.append(f"  {answer}: {votes} vote(s)")
    
    # Join all steps into a single string
    calculation_text = "\n".join(calculation_steps)
    
    return votes_per_answer, calculation_text

def plot_question_results(question, percentages, vote_allocation, total_responses, no_opinion_count, calculation_text, output_dir='plots'):
    """
    Create visualizations for a question showing:
    1. A pie chart for percentages of each answer
    2. A pie chart for the 3-vote allocation
    3. Step-by-step calculation of the vote allocation
    With enhanced aesthetics and the question displayed on the figure.
    """
    if not percentages:
        return
    
    # Calculate total number of responses (valid + no opinion)
    total_number_of_responses = total_responses + no_opinion_count
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a figure with a proper title area and space for calculation text
    fig = plt.figure(figsize=(18, 12))
    
    # Define a grid layout
    gs = fig.add_gridspec(3, 3)
    
    # Add a title for the entire figure containing the question
    # Wrap the question text for better readability
    wrapped_question = "\n".join(textwrap.wrap(question, width=80))
    fig.suptitle(wrapped_question, fontsize=14, fontweight='bold', y=0.98)
    
    # Create the pie chart subplots
    ax1 = fig.add_subplot(gs[0:2, 0:2])  # Percentage pie chart (larger)
    ax2 = fig.add_subplot(gs[0:2, 2])    # Vote allocation pie chart
    
    # Create a text box for the calculation steps
    ax_text = fig.add_subplot(gs[2, :])
    ax_text.axis('off')  # Hide axes
    
    # Prepare the data for the first subplot (percentages)
    answers = list(percentages.keys())
    pcts = list(percentages.values())
    
    # Create simplified labels for the pie chart
    simplified_labels = []
    for answer in answers:
        if "YES" in answer.upper():
            simplified_labels.append("Yes")
        elif "NO" in answer.upper() and "OPINION" not in answer.upper():
            simplified_labels.append("No")
        elif "ABSTAIN" in answer.upper():
            simplified_labels.append("Abstain")
        else:
            simplified_labels.append(answer)  # Keep original if no match
    
    # Sort by percentage in descending order for better labeling
    sorted_indices = np.argsort(pcts)[::-1]
    answers = [answers[i] for i in sorted_indices]
    simplified_labels = [simplified_labels[i] for i in sorted_indices]
    pcts = [pcts[i] for i in sorted_indices]
    
    # Assign specific colors for Yes, No, and Abstain
    color_map = {
        'Yes': '#2ecc71',  # Green
        'No': '#e74c3c',   # Red
        'Abstain': '#95a5a6',  # Gray
    }
    
    # Generate a list of colors for each answer
    colors = []
    # Keep track of how many custom colors we've used
    custom_color_count = 0
    
    for label in simplified_labels:
        if label in color_map:
            colors.append(color_map[label])
        else:
            # Generate a color from plasma palette for other answers
            custom_color_count += 1
            colors.append(plt.cm.plasma(0.1 + 0.8 * custom_color_count / (len(answers) + 1)))
    
    # Explode the largest slice slightly for emphasis
    explode = [0.05 if i == 0 else 0 for i in range(len(answers))]
    
    # Plot percentages as a pie chart with enhanced visuals (no shadow)
    wedges, texts, autotexts = ax1.pie(
        pcts, 
        labels=simplified_labels, 
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        explode=explode,
        shadow=False,  # Remove shadow effect
        wedgeprops={'edgecolor': 'w', 'linewidth': 1, 'alpha': 0.9},
        textprops={'fontsize': 11}
    )
    
    # Format the pie chart labels and percentages
    plt.setp(autotexts, size=11, weight="bold", color='white')
    plt.setp(texts, size=10)
    
    # Add a slight frame to the plot for better appearance
    for axis in [ax1, ax2]:
        axis.spines['top'].set_visible(True)
        axis.spines['right'].set_visible(True)
        axis.spines['bottom'].set_visible(True)
        axis.spines['left'].set_visible(True)
        axis.set_facecolor('#f9f9f9')
    
    # Set title with all response counts
    ax1.set_title(f'Response Distribution\nTotal Responses: {total_number_of_responses} | Considered Responses: {total_responses} | NO OPINION: {no_opinion_count}', 
                 fontsize=12, pad=10)
    
    # Create a clean circle in the middle for better aesthetics
    circle = plt.Circle((0,0), 0.3, fc='white')
    ax1.add_artist(circle)
    
    # Prepare the data for the second subplot (3-vote allocation)
    vote_answers = list(vote_allocation.keys())
    vote_counts = list(vote_allocation.values())
    
    # Create simplified labels for vote allocation
    vote_simplified_labels = []
    for answer in vote_answers:
        if "YES" in answer.upper():
            vote_simplified_labels.append("Yes")
        elif "NO" in answer.upper() and "OPINION" not in answer.upper():
            vote_simplified_labels.append("No")
        elif "ABSTAIN" in answer.upper():
            vote_simplified_labels.append("Abstain")
        else:
            vote_simplified_labels.append(answer)  # Keep original if no match
    
    # Filter to only include answers with votes
    nonzero_indices = [i for i, count in enumerate(vote_counts) if count > 0]
    vote_answers = [vote_answers[i] for i in nonzero_indices]
    vote_simplified_labels = [vote_simplified_labels[i] for i in nonzero_indices]
    vote_counts = [vote_counts[i] for i in nonzero_indices]
    
    if vote_counts:  # Only create the pie if there are votes
        # Generate colors for the vote pie chart (match colors with simplified labels)
        vote_colors = []
        for label in vote_simplified_labels:
            if label in color_map:
                vote_colors.append(color_map[label])
            else:
                # Try to match with the first pie chart colors if possible
                try:
                    idx = simplified_labels.index(label)
                    vote_colors.append(colors[idx])
                except ValueError:
                    # Use a default color if not found
                    vote_colors.append(plt.cm.plasma(0.5))
        
        # Plot vote allocation as a pie chart (no shadow)
        vote_wedges, vote_texts, vote_autotexts = ax2.pie(
            vote_counts,
            labels=vote_simplified_labels,
            autopct=lambda p: f'{int(p * sum(vote_counts) / 100)}',  # Show actual vote count
            colors=vote_colors,
            startangle=90,
            shadow=False,  # Remove shadow effect
            wedgeprops={'edgecolor': 'w', 'linewidth': 1, 'alpha': 0.9},
            textprops={'fontsize': 11}
        )
        
        # Format the pie chart labels and counts
        plt.setp(vote_autotexts, size=13, weight="bold", color='white')
        plt.setp(vote_texts, size=11)
        
        # Create a clean circle in the middle for better aesthetics
        vote_circle = plt.Circle((0,0), 0.3, fc='white')
        ax2.add_artist(vote_circle)
    
    # Set title for the vote allocation
    ax2.set_title('3-Vote Allocation', fontsize=12, pad=10)
    
    # Add a legend outside the plots for better readability if there are many answers
    if len(answers) > 3:
        handles = [plt.Rectangle((0,0),1,1, color=colors[i]) for i in range(len(simplified_labels))]
        legend = fig.legend(handles, simplified_labels, 
                           loc='upper center', 
                           bbox_to_anchor=(0.5, 0.32),
                           ncol=min(5, len(simplified_labels)),
                           frameon=True,
                           facecolor='white',
                           edgecolor='lightgray',
                           fontsize=10)
    
    # Add the calculation text to the text box
    ax_text.text(0.01, 0.99, calculation_text, 
                 transform=ax_text.transAxes,
                 verticalalignment='top',
                 horizontalalignment='left',
                 fontfamily='monospace',
                 fontsize=10,
                 bbox=dict(boxstyle='round,pad=1', facecolor='#f8f9fa', edgecolor='#dcdcdc', alpha=0.9))
    
    # Add descriptive title for the calculation section
    ax_text.text(0.5, 1.05, 'Step-by-Step Calculation of 3-Vote Allocation using Largest Remainder Method', 
                 transform=ax_text.transAxes,
                 verticalalignment='center',
                 horizontalalignment='center',
                 fontsize=12,
                 fontweight='bold')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])  # Make room for the title
    
    # Clean up question text for filename
    question_clean = question.replace(':', '_').replace('?', '').replace(' ', '_')[:50]
    file_path = os.path.join(output_dir, f'{question_clean}.png')
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return file_path

def main():
    # Check for proper command-line arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python analyze_survey.py <csv_file_path> [output_directory]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Set output directory (default or user-specified)
    output_dir = 'plots'
    if len(sys.argv) == 3:
        output_dir = sys.argv[2]
    
    print(f"Processing survey data from: {file_path}")
    print(f"Results will be saved to: {output_dir}")
    
    # Read survey data
    survey_data = read_survey_data(file_path)
    
    # Process each question (skip the first 3 columns which are metadata)
    questions = survey_data.columns[3:]
    
    # Store results for summary
    results = []
    
    for question in questions:
        print(f"\nAnalyzing question: {question}")
        
        # Analyze the question
        counts, percentages, total_responses, no_opinion_count = analyze_question(survey_data, question)
        
        if not percentages:
            print(f"  No valid responses for this question.")
            continue
        
        # Calculate total number of responses
        total_number_of_responses = total_responses + no_opinion_count
        
        # Print response counts
        print(f"  Total Number of responses: {total_number_of_responses}")
        print(f"  Considered responses: {total_responses}")
        print(f"  'NO OPINION' responses: {no_opinion_count}")
        print("  Response percentages:")
        for answer, pct in sorted(percentages.items(), key=lambda x: x[1], reverse=True):
            print(f"    {answer}: {pct:.1f}%")
        
        # Allocate 3 votes with calculation steps
        vote_allocation, calculation_text = allocate_three_votes(percentages)
        
        # Print vote allocation
        print("  3-vote allocation:")
        for answer, votes in sorted(vote_allocation.items(), key=lambda x: x[1], reverse=True):
            if votes > 0:
                print(f"    {answer}: {votes} vote(s)")
        
        # Plot the results with the specified output directory
        plot_file = plot_question_results(question, percentages, vote_allocation, total_responses, 
                                         no_opinion_count, calculation_text, output_dir=output_dir)
        
        # Save results for summary
        results.append({
            'question': question,
            'percentages': percentages,
            'vote_allocation': vote_allocation,
            'total_responses': total_responses,
            'no_opinion_count': no_opinion_count,
            'calculation_text': calculation_text,
            'plot_file': plot_file
        })
    
    print(f"\nAnalysis complete. Plots saved in the '{output_dir}' directory.")

if __name__ == "__main__":
    main() 