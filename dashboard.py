# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import calendar
from database import CallAnalysisDB

st.set_page_config(
    page_title="Call Analysis Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #212529;
    }
    .agent-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 0.5rem;
    }
    .performance-indicator {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .performance-excellent { background-color: #d4edda; color: #155724; }
    .performance-good { background-color: #d1ecf1; color: #0c5460; }
    .performance-average { background-color: #fff3cd; color: #856404; }
    .performance-poor { background-color: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_database():
    return CallAnalysisDB()

db = init_database()

# Title
st.markdown('<h1 class="main-header">📊 Call Analysis Dashboard</h1>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.title("🔍 Filters")

# Date range filter
date_range = st.sidebar.date_input(
    "Date Range",
    value=(date.today() - timedelta(days=90), date.today()),
    max_value=date.today()
)

start_date = date_range[0] if len(date_range) > 0 else date.today() - timedelta(days=90)
end_date = date_range[1] if len(date_range) > 1 else date.today()

# Agent filter
all_agents = db.get_all_agents()
selected_agents = st.sidebar.multiselect(
    "Select Agents",
    options=all_agents,
    default=all_agents[:5] if len(all_agents) > 5 else all_agents,
    help="Leave empty to include all agents"
)

# Dashboard type
dashboard_type = st.sidebar.selectbox(
    "Dashboard View",
    ["Overview", "Agent Performance", "Monthly Trends", "Category Analysis", "Individual Agent"]
)

# Load dashboard data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_dashboard_data(start_date, end_date):
    return db.get_dashboard_data(start_date, end_date)

dashboard_data = load_dashboard_data(start_date, end_date)

def get_performance_class(score):
    """Get CSS class for performance indicator"""
    if score >= 0.8:
        return "performance-excellent"
    elif score >= 0.6:
        return "performance-good"
    elif score >= 0.4:
        return "performance-average"
    else:
        return "performance-poor"

def get_performance_text(score):
    """Get performance text"""
    if score >= 0.8:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    elif score >= 0.4:
        return "Average"
    else:
        return "Needs Improvement"

# Overview Dashboard
if dashboard_type == "Overview":
    st.subheader("📈 Performance Overview")
    
    # Key metrics
    overview = dashboard_data['overview']
    if overview:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Total Agents</div>
                    <div class="metric-value">{overview.get('total_agents', 0)}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Total Calls</div>
                    <div class="metric-value">{overview.get('total_calls', 0)}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col3:
            rule_score = overview.get('avg_rule_score', 0) or 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Avg Rule Score</div>
                    <div class="metric-value">{rule_score:.2f}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col4:
            nlp_score = overview.get('avg_nlp_score', 0) or 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Avg NLP Score</div>
                    <div class="metric-value">{nlp_score:.2f}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col5:
            total_hours = (overview.get('total_duration_minutes', 0) or 0) / 60
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Total Hours</div>
                    <div class="metric-value">{total_hours:.1f}h</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Monthly Call Volume")
        monthly_data = dashboard_data['monthly_trends']
        if not monthly_data.empty:
            fig = px.line(
                monthly_data, 
                x='month', 
                y='total_calls',
                title="Calls per Month",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Number of Calls",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No call data available for the selected period.")
    
    with col2:
        st.subheader("📈 Average Scores Trend")
        if not monthly_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_data['month'],
                y=monthly_data['avg_rule_score'],
                mode='lines+markers',
                name='Rule-based',
                line=dict(color='#1f77b4')
            ))
            fig.add_trace(go.Scatter(
                x=monthly_data['month'],
                y=monthly_data['avg_nlp_score'],
                mode='lines+markers',
                name='NLP Enhanced',
                line=dict(color='#ff7f0e')
            ))
            fig.update_layout(
                title="Average Scores Over Time",
                xaxis_title="Month",
                yaxis_title="Average Score",
                hovermode='x unified',
                yaxis=dict(range=[0, 1])
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No scoring data available for the selected period.")

# Agent Performance Dashboard
elif dashboard_type == "Agent Performance":
    st.subheader("👥 Agent Performance Comparison")
    
    agent_data = dashboard_data['agent_performance']
    if not agent_data.empty:
        # Filter by selected agents if any
        if selected_agents:
            agent_data = agent_data[agent_data['agent_name'].isin(selected_agents)]
        
        # Agent performance cards
        st.subheader("🎯 Top Performers")
        
        # Sort by rule score
        top_agents = agent_data.nlargest(6, 'avg_rule_score')
        
        cols = st.columns(3)
        for idx, (_, agent) in enumerate(top_agents.iterrows()):
            with cols[idx % 3]:
                rule_score = agent['avg_rule_score'] or 0
                nlp_score = agent['avg_nlp_score'] or 0
                
                performance_class = get_performance_class(rule_score)
                performance_text = get_performance_text(rule_score)
                
                st.markdown(
                    f"""
                    <div class="agent-card">
                        <h4>{agent['agent_name']}</h4>
                        <div><strong>Department:</strong> {agent['department'] or 'N/A'}</div>
                        <div><strong>Calls:</strong> {int(agent['total_calls'] or 0)}</div>
                        <div><strong>Rule Score:</strong> {rule_score:.2f}</div>
                        <div><strong>NLP Score:</strong> {nlp_score:.2f}</div>
                        <div><span class="performance-indicator {performance_class}">{performance_text}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Detailed comparison chart
        st.subheader("📊 Detailed Agent Comparison")
        
        # Create comparison chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Rule-based Scores', 'NLP Enhanced Scores', 'Call Volume', 'Sentiment Distribution'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Rule-based scores
        fig.add_trace(
            go.Bar(
                x=agent_data['agent_name'],
                y=agent_data['avg_rule_score'],
                name='Rule Score',
                marker_color='#1f77b4'
            ),
            row=1, col=1
        )
        
        # NLP scores
        fig.add_trace(
            go.Bar(
                x=agent_data['agent_name'],
                y=agent_data['avg_nlp_score'],
                name='NLP Score',
                marker_color='#ff7f0e'
            ),
            row=1, col=2
        )
        
        # Call volume
        fig.add_trace(
            go.Bar(
                x=agent_data['agent_name'],
                y=agent_data['total_calls'],
                name='Total Calls',
                marker_color='#2ca02c'
            ),
            row=2, col=1
        )
        
        # Sentiment pie chart (aggregated)
        total_positive = agent_data['positive_calls'].sum()
        total_negative = agent_data['negative_calls'].sum()
        total_neutral = agent_data['total_calls'].sum() - total_positive - total_negative
        
        fig.add_trace(
            go.Pie(
                labels=['Positive', 'Negative', 'Neutral'],
                values=[total_positive, total_negative, total_neutral],
                name="Sentiment"
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed data table
        st.subheader("📋 Detailed Agent Statistics")
        
        # Format the dataframe for display
        display_df = agent_data.copy()
        display_df['avg_rule_score'] = display_df['avg_rule_score'].round(3)
        display_df['avg_nlp_score'] = display_df['avg_nlp_score'].round(3)
        display_df['total_duration_hours'] = (display_df['total_duration_minutes'] / 60).round(1)
        display_df['positive_rate'] = (display_df['positive_calls'] / display_df['total_calls'] * 100).round(1)
        
        # Select columns for display
        display_columns = [
            'agent_name', 'department', 'total_calls', 'avg_rule_score', 
            'avg_nlp_score', 'total_duration_hours', 'positive_rate'
        ]
        
        st.dataframe(
            display_df[display_columns].rename(columns={
                'agent_name': 'Agent Name',
                'department': 'Department', 
                'total_calls': 'Total Calls',
                'avg_rule_score': 'Rule Score',
                'avg_nlp_score': 'NLP Score',
                'total_duration_hours': 'Total Hours',
                'positive_rate': 'Positive Rate %'
            }),
            use_container_width=True
        )
    else:
        st.info("No agent performance data available for the selected period.")

# Monthly Trends Dashboard
elif dashboard_type == "Monthly Trends":
    st.subheader("📅 Monthly Performance Trends")
    
    # Get monthly data by agent
    monthly_agent_data = pd.DataFrame()
    for agent in selected_agents or all_agents:
        agent_monthly = db.get_agent_scores_by_month(agent_name=agent)
        if not agent_monthly.empty:
            monthly_agent_data = pd.concat([monthly_agent_data, agent_monthly], ignore_index=True)
    
    if not monthly_agent_data.empty:
        # Create month-year column for better sorting
        monthly_agent_data['month_year'] = monthly_agent_data.apply(
            lambda row: f"{row['year']}-{row['month']:02d}", axis=1
        )
        monthly_agent_data['month_name'] = monthly_agent_data.apply(
            lambda row: f"{calendar.month_abbr[row['month']]} {row['year']}", axis=1
        )
        
        # Overall trends
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Score Trends by Agent")
            fig = px.line(
                monthly_agent_data,
                x='month_name',
                y='avg_rule_score',
                color='agent_name',
                title="Rule-based Scores Over Time",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Average Rule Score",
                yaxis=dict(range=[0, 1]),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🧠 NLP Score Trends")
            fig = px.line(
                monthly_agent_data,
                x='month_name',
                y='avg_nlp_score',
                color='agent_name',
                title="NLP Enhanced Scores Over Time",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Average NLP Score",
                yaxis=dict(range=[0, 1]),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Call volume trends
        st.subheader("📞 Call Volume Trends")
        fig = px.bar(
            monthly_agent_data,
            x='month_name',
            y='total_calls',
            color='agent_name',
            title="Monthly Call Volume by Agent",
            barmode='group'
        )
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Calls",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap of performance
        st.subheader("🔥 Performance Heatmap")
        
        # Pivot data for heatmap
        heatmap_data = monthly_agent_data.pivot(
            index='agent_name', 
            columns='month_name', 
            values='avg_rule_score'
        )
        
        if not heatmap_data.empty:
            fig = px.imshow(
                heatmap_data,
                title="Agent Performance Heatmap (Rule-based Scores)",
                color_continuous_scale="RdYlGn",
                aspect="auto"
            )
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Agent"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Monthly summary table
        st.subheader("📋 Monthly Summary Table")
        summary_table = monthly_agent_data.groupby('month_name').agg({
            'total_calls': 'sum',
            'avg_rule_score': 'mean',
            'avg_nlp_score': 'mean',
            'total_duration_minutes': 'sum',
            'positive_sentiment_count': 'sum',
            'negative_sentiment_count': 'sum'
        }).round(3)
        
        summary_table['total_duration_hours'] = (summary_table['total_duration_minutes'] / 60).round(1)
        summary_table['positive_rate%'] = (
            summary_table['positive_sentiment_count'] / summary_table['total_calls'] * 100
        ).round(1)
        
        st.dataframe(
            summary_table[['total_calls', 'avg_rule_score', 'avg_nlp_score', 
                          'total_duration_hours', 'positive_rate%']].rename(columns={
                'total_calls': 'Total Calls',
                'avg_rule_score': 'Avg Rule Score',
                'avg_nlp_score': 'Avg NLP Score',
                'total_duration_hours': 'Total Hours',
                'positive_rate%': 'Positive Rate %'
            }),
            use_container_width=True
        )
    else:
        st.info("No monthly trend data available for the selected agents and period.")

# Category Analysis Dashboard
elif dashboard_type == "Category Analysis":
    st.subheader("📊 QA Category Performance Analysis")
    
    category_data = dashboard_data['category_breakdown']
    if not category_data.empty:
        # Overall category performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Rule-based Category Scores")
            rule_data = category_data[category_data['scoring_method'] == 'rule_based']
            
            if not rule_data.empty:
                fig = px.bar(
                    rule_data,
                    x='category',
                    y='avg_score',
                    title="Average Scores by Category (Rule-based)",
                    color='avg_score',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(
                    xaxis_title="Category",
                    yaxis_title="Average Score",
                    yaxis=dict(range=[0, 1]),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🧠 NLP Enhanced Category Scores")
            nlp_data = category_data[category_data['scoring_method'] == 'nlp_enhanced']
            
            if not nlp_data.empty:
                fig = px.bar(
                    nlp_data,
                    x='category',
                    y='avg_score',
                    title="Average Scores by Category (NLP Enhanced)",
                    color='avg_score',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(
                    xaxis_title="Category",
                    yaxis_title="Average Score",
                    yaxis=dict(range=[0, 1]),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Comparison chart
        st.subheader("⚖️ Scoring Method Comparison")
        
        # Merge rule and NLP data for comparison
        comparison_data = pd.merge(
            rule_data[['category', 'avg_score']].rename(columns={'avg_score': 'rule_score'}),
            nlp_data[['category', 'avg_score']].rename(columns={'avg_score': 'nlp_score'}),
            on='category',
            how='outer'
        ).fillna(0)
        
        if not comparison_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=comparison_data['category'],
                y=comparison_data['rule_score'],
                name='Rule-based',
                marker_color='#1f77b4'
            ))
            fig.add_trace(go.Bar(
                x=comparison_data['category'],
                y=comparison_data['nlp_score'],
                name='NLP Enhanced',
                marker_color='#ff7f0e'
            ))
            
            fig.update_layout(
                title="Rule-based vs NLP Enhanced Scoring by Category",
                xaxis_title="Category",
                yaxis_title="Average Score",
                barmode='group',
                yaxis=dict(range=[0, 1]),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Category insights
        st.subheader("💡 Category Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Best performing category
            if not rule_data.empty:
                best_category = rule_data.loc[rule_data['avg_score'].idxmax()]
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-title">Best Performing Category</div>
                        <div class="metric-value">{best_category['category']}</div>
                        <div>Score: {best_category['avg_score']:.3f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        with col2:
            # Most improved (NLP vs Rule)
            if not comparison_data.empty:
                comparison_data['improvement'] = comparison_data['nlp_score'] - comparison_data['rule_score']
                most_improved = comparison_data.loc[comparison_data['improvement'].idxmax()]
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-title">Most Improved (NLP vs Rule)</div>
                        <div class="metric-value">{most_improved['category']}</div>
                        <div>Improvement: +{most_improved['improvement']:.3f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        with col3:
            # Needs attention
            if not rule_data.empty:
                worst_category = rule_data.loc[rule_data['avg_score'].idxmin()]
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-title">Needs Attention</div>
                        <div class="metric-value">{worst_category['category']}</div>
                        <div>Score: {worst_category['avg_score']:.3f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Detailed category table
        st.subheader("📋 Detailed Category Statistics")
        st.dataframe(
            category_data.rename(columns={
                'category': 'Category',
                'scoring_method': 'Scoring Method',
                'avg_score': 'Average Score',
                'total_evaluations': 'Total Evaluations'
            }),
            use_container_width=True
        )
    else:
        st.info("No category analysis data available for the selected period.")

# Individual Agent Dashboard
elif dashboard_type == "Individual Agent":
    st.subheader("👤 Individual Agent Analysis")
    
    # Agent selector
    if all_agents:
        selected_agent = st.selectbox("Select Agent", all_agents)
        
        if selected_agent:
            # Get agent's monthly data
            agent_monthly = db.get_agent_scores_by_month(agent_name=selected_agent)
            
            if not agent_monthly.empty:
                # Agent overview metrics
                latest_month = agent_monthly.iloc[0]  # Most recent month
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-title">Latest Rule Score</div>
                            <div class="metric-value">{latest_month['avg_rule_score']:.3f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-title">Latest NLP Score</div>
                            <div class="metric-value">{latest_month['avg_nlp_score']:.3f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col3:
                    total_calls = agent_monthly['total_calls'].sum()
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-title">Total Calls</div>
                            <div class="metric-value">{total_calls}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col4:
                    total_hours = agent_monthly['total_duration_minutes'].sum() / 60
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-title">Total Hours</div>
                            <div class="metric-value">{total_hours:.1f}h</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Performance trend charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📈 Score Progression")
                    
                    # Create month labels
                    agent_monthly['month_label'] = agent_monthly.apply(
                        lambda row: f"{calendar.month_abbr[row['month']]} {row['year']}", axis=1
                    )
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=agent_monthly['month_label'],
                        y=agent_monthly['avg_rule_score'],
                        mode='lines+markers',
                        name='Rule Score',
                        line=dict(color='#1f77b4', width=3)
                    ))
                    fig.add_trace(go.Scatter(
                        x=agent_monthly['month_label'],
                        y=agent_monthly['avg_nlp_score'],
                        mode='lines+markers',
                        name='NLP Score',
                        line=dict(color='#ff7f0e', width=3)
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_agent}'s Score Progression",
                        xaxis_title="Month",
                        yaxis_title="Score",
                        yaxis=dict(range=[0, 1]),
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("📞 Call Volume & Sentiment")
                    
                    # Calculate sentiment percentages
                    agent_monthly['positive_pct'] = (
                        agent_monthly['positive_sentiment_count'] / agent_monthly['total_calls'] * 100
                    ).fillna(0)
                    agent_monthly['negative_pct'] = (
                        agent_monthly['negative_sentiment_count'] / agent_monthly['total_calls'] * 100
                    ).fillna(0)
                    
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Call volume bars
                    fig.add_trace(
                        go.Bar(
                            x=agent_monthly['month_label'],
                            y=agent_monthly['total_calls'],
                            name='Calls',
                            marker_color='#2ca02c',
                            opacity=0.7
                        ),
                        secondary_y=False
                    )
                    
                    # Positive sentiment line
                    fig.add_trace(
                        go.Scatter(
                            x=agent_monthly['month_label'],
                            y=agent_monthly['positive_pct'],
                            mode='lines+markers',
                            name='Positive %',
                            line=dict(color='#d62728', width=2)
                        ),
                        secondary_y=True
                    )
                    
                    fig.update_layout(title=f"{selected_agent}'s Call Volume & Sentiment")
                    fig.update_xaxes(title_text="Month")
                    fig.update_yaxes(title_text="Number of Calls", secondary_y=False)
                    fig.update_yaxes(title_text="Positive Sentiment %", secondary_y=True)
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Monthly performance table
                st.subheader("📋 Monthly Performance Detail")
                
                display_df = agent_monthly.copy()
                display_df = display_df.sort_values(['year', 'month'], ascending=False)
                display_df['month_name'] = display_df.apply(
                    lambda row: f"{calendar.month_name[row['month']]} {row['year']}", axis=1
                )
                display_df['avg_rule_score'] = display_df['avg_rule_score'].round(3)
                display_df['avg_nlp_score'] = display_df['avg_nlp_score'].round(3)
                display_df['total_duration_hours'] = (display_df['total_duration_minutes'] / 60).round(1)
                
                st.dataframe(
                    display_df[['month_name', 'total_calls', 'avg_rule_score', 'avg_nlp_score',
                               'total_duration_hours', 'positive_sentiment_count', 'negative_sentiment_count']].rename(columns={
                        'month_name': 'Month',
                        'total_calls': 'Calls',
                        'avg_rule_score': 'Rule Score',
                        'avg_nlp_score': 'NLP Score',
                        'total_duration_hours': 'Hours',
                        'positive_sentiment_count': 'Positive',
                        'negative_sentiment_count': 'Negative'
                    }),
                    use_container_width=True
                )
            else:
                st.info(f"No data available for {selected_agent} in the selected period.")
    else:
        st.info("No agents found in the database.")

# Data management section
st.sidebar.markdown("---")
st.sidebar.subheader("🗄️ Data Management")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Export options
if st.sidebar.button("📊 Export Dashboard Data"):
    # Create export data
    export_data = {
        'overview': dashboard_data['overview'],
        'agent_performance': dashboard_data['agent_performance'].to_dict('records'),
        'monthly_trends': dashboard_data['monthly_trends'].to_dict('records'),
        'category_breakdown': dashboard_data['category_breakdown'].to_dict('records')
    }
    
    import json
    st.sidebar.download_button(
        label="💾 Download JSON",
        data=json.dumps(export_data, indent=2, default=str),
        file_name=f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

# Database info
with st.sidebar.expander("ℹ️ Database Info"):
    st.markdown(f"""
    **Database:** {db.db_path}
    **Total Agents:** {len(all_agents)}
    **Date Range:** {start_date} to {end_date}
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

# Help section
with st.sidebar.expander("❓ Dashboard Help"):
    st.markdown("""
    **Dashboard Views:**
    - **Overview:** High-level metrics and trends
    - **Agent Performance:** Compare agent scores
    - **Monthly Trends:** Track performance over time
    - **Category Analysis:** QA category breakdown
    - **Individual Agent:** Detailed agent view
    
    **Filters:**
    - Use date range to focus analysis
    - Select specific agents for comparison
    - Data auto-refreshes every 5 minutes
    
    **Performance Indicators:**
    - 🟢 Excellent: ≥80%
    - 🔵 Good: 60-79%
    - 🟡 Average: 40-59%
    - 🔴 Needs Improvement: <40%
    """)