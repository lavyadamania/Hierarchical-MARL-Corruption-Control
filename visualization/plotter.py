import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from config import RESULTS_DIR, DPI, FIG_SIZE_WIDE, FIG_SIZE_SQUARE

class Plotter:
    def __init__(self, db_manager):
        self.db = db_manager
        # Ensure results dir exists
        os.makedirs(RESULTS_DIR, exist_ok=True)
        sns.set_style("darkgrid")

    def generate_all(self):
        """Generates all 5 required visualizations."""
        print("Generating visualizations...")
        self.plot_corruption_hierarchy()
        self.plot_success_rate()
        self.plot_cop_performance()
        self.plot_investigations()
        self.plot_witness_impact()
        print(f"Visualizations saved to {RESULTS_DIR}")

    def plot_corruption_hierarchy(self):
        """1. Bar chart: Average corruption by rank"""
        query = "SELECT rank, AVG(corruption_score) as avg_corr FROM cops GROUP BY rank"
        df = pd.read_sql_query(query, self.db.get_connection())
        
        plt.figure(figsize=FIG_SIZE_WIDE)
        # Custom color map logic
        colors = ['gold' if r in ['chief', 'detective'] else 'crimson' for r in df['rank']]
        
        sns.barplot(data=df, x='rank', y='avg_corr', hue='rank', palette=dict(zip(df['rank'], colors)), legend=False)
        plt.title('Average Corruption by Rank')
        plt.ylim(0, 100)
        plt.ylabel('Corruption Score')
        plt.savefig(os.path.join(RESULTS_DIR, 'corruption_hierarchy.png'), dpi=DPI)
        plt.close()

    def plot_success_rate(self):
        """2. Pie chart: Bribe outcomes distribution"""
        query = "SELECT outcome, COUNT(*) as count FROM bribe_history GROUP BY outcome"
        df = pd.read_sql_query(query, self.db.get_connection())
        
        if df.empty:
            return

        plt.figure(figsize=FIG_SIZE_SQUARE)
        colors = {'success': 'green', 'caught': 'red', 'rejected': 'gray'}
        # Map colors to data
        pie_colors = [colors.get(x, 'blue') for x in df['outcome']]
        
        plt.pie(df['count'], labels=df['outcome'], autopct='%1.1f%%', colors=pie_colors)
        plt.title('Bribe Outcomes Distribution')
        plt.savefig(os.path.join(RESULTS_DIR, 'success_rate.png'), dpi=DPI)
        plt.close()

    def plot_cop_performance(self):
        """3. Grouped bar chart per cop: Bribes taken vs Times caught"""
        query = "SELECT name, times_bribed, times_caught FROM cops WHERE cop_type='corrupt'"
        df = pd.read_sql_query(query, self.db.get_connection())
        
        if df.empty:
            return

        # Melt for seaborn grouped bar
        df_melt = df.melt(id_vars='name', value_vars=['times_bribed', 'times_caught'], 
                          var_name='Metric', value_name='Count')
        
        plt.figure(figsize=FIG_SIZE_WIDE)
        sns.barplot(data=df_melt, x='name', y='Count', hue='Metric', 
                    palette={'times_bribed': 'green', 'times_caught': 'red'})
        plt.title('Corrupt Cop Performance')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'cop_performance.png'), dpi=DPI)
        plt.close()

    def plot_investigations(self):
        """4. Bar chart: Investigation outcomes"""
        query = "SELECT outcome, COUNT(*) as count FROM investigations GROUP BY outcome"
        df = pd.read_sql_query(query, self.db.get_connection())
        
        if df.empty:
            return

        plt.figure(figsize=FIG_SIZE_WIDE)
        sns.barplot(data=df, x='outcome', y='count')
        plt.title('Investigation Outcomes')
        plt.savefig(os.path.join(RESULTS_DIR, 'investigations.png'), dpi=DPI)
        plt.close()

    def plot_witness_impact(self):
        """5. Line graph: Success rate vs witness count"""
        # Calculate success rate manually: success / (success + caught) for each witness count
        # Ignoring rejected
        query = """
        SELECT witness_count, 
               SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as successes,
               SUM(CASE WHEN outcome='caught' THEN 1 ELSE 0 END) as caughts
        FROM bribe_history 
        WHERE outcome IN ('success', 'caught')
        GROUP BY witness_count
        """
        df = pd.read_sql_query(query, self.db.get_connection())
        
        if df.empty:
            return
            
        df['total'] = df['successes'] + df['caughts']
        df['success_rate'] = (df['successes'] / df['total']) * 100
        
        plt.figure(figsize=FIG_SIZE_WIDE)
        sns.lineplot(data=df, x='witness_count', y='success_rate', marker='o')
        plt.fill_between(df['witness_count'], df['success_rate'], alpha=0.3)
        plt.title('Bribe Success Rate vs Witness Count')
        plt.ylabel('Success Rate (%)')
        plt.xlabel('Witness Count')
        plt.ylim(0, 100)
        plt.xticks(range(0, 5)) # 0-4
        plt.savefig(os.path.join(RESULTS_DIR, 'witness_impact.png'), dpi=DPI)
        plt.close()
