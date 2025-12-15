"""
Example 04: Data Analysis Workflow

This example demonstrates how to use the data analyst agent with database
queries and data transformation tools.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the data analysis workflow example."""
    print("=" * 60)
    print("Example 04: Data Analysis Workflow")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Load data-analyst agent
        print("\n1. Loading data-analyst agent...")
        response = await client.get("/agents/data-analyst")
        if response.status_code == 200:
            agent = response.json()
            print(f"   Found: {agent['name']}")
        else:
            print("   Agent not found.")
            return
        
        # 2. Load required tools
        print("\n2. Loading tools...")
        tools = ['database-query', 'data-transformer', 'file-operations']
        for tool_id in tools:
            response = await client.get(f"/tools/{tool_id}")
            if response.status_code == 200:
                tool = response.json()
                print(f"   ✓ {tool['name']}")
        
        # 3. Load skills
        print("\n3. Loading skills...")
        skills = ['sql-generation']
        for skill_id in skills:
            response = await client.get(f"/repository/skills/{skill_id}")
            if response.status_code == 200:
                skill = response.json()
                print(f"   ✓ {skill['name']}: {skill['description'][:40]}...")
        
        # 4. Show workflow
        print("\n4. Data Analysis Workflow:")
        print("""
   User Request: "Analyze sales trends over the last quarter"
   
   ┌────────────────────────────────────────────────────────┐
   │ Step 1: Natural Language → SQL (sql-generation skill) │
   └────────────────────────────────────────────────────────┘
   │
   │  Generated SQL:
   │  SELECT 
   │      DATE_TRUNC('week', order_date) as week,
   │      SUM(total_amount) as revenue,
   │      COUNT(*) as order_count
   │  FROM orders
   │  WHERE order_date >= CURRENT_DATE - INTERVAL '3 months'
   │  GROUP BY DATE_TRUNC('week', order_date)
   │  ORDER BY week;
   │
   ▼
   ┌────────────────────────────────────────────────────────┐
   │ Step 2: Execute Query (database-query tool)           │
   └────────────────────────────────────────────────────────┘
   │
   │  Returns: JSON array of weekly data
   │
   ▼
   ┌────────────────────────────────────────────────────────┐
   │ Step 3: Transform Data (data-transformer tool)        │
   └────────────────────────────────────────────────────────┘
   │
   │  - Calculate week-over-week growth
   │  - Identify outliers
   │  - Compute moving averages
   │
   ▼
   ┌────────────────────────────────────────────────────────┐
   │ Step 4: Statistical Analysis (data-analyst agent)     │
   └────────────────────────────────────────────────────────┘
   │
   │  - Trend analysis
   │  - Correlation calculations
   │  - Confidence intervals
   │
   ▼
   ┌────────────────────────────────────────────────────────┐
   │ Step 5: Generate Report (file-operations tool)        │
   └────────────────────────────────────────────────────────┘
""")
        
        # 5. Example output
        print("5. Example Analysis Output:")
        print("""
   ┌─────────────────────────────────────────────────────────┐
   │            Q3 2024 Sales Trend Analysis                │
   ├─────────────────────────────────────────────────────────┤
   │ Summary:                                                │
   │   Total Revenue: $1,234,567                            │
   │   Total Orders: 4,521                                  │
   │   Avg Order Value: $273.12                             │
   │                                                         │
   │ Key Findings:                                           │
   │   • Revenue grew 12.3% compared to Q2                  │
   │   • Week 8 showed anomaly (+45% spike) - promotion     │
   │   • Strong correlation (r=0.87) between marketing      │
   │     spend and order volume                              │
   │                                                         │
   │ Recommendations:                                        │
   │   1. Increase marketing during weeks 3-5               │
   │   2. Consider similar promotions for Q4                │
   │   3. Focus on high-value customer segments             │
   └─────────────────────────────────────────────────────────┘
""")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
