import streamlit as st
import pandas as pd
import datetime
import logging
from typing import Optional

from src.data_collector import DataCollector
from src.config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{Config.APP_NAME} - Análise de Commits", 
    page_icon="📊", 
    layout="wide"
)
st.title(f"{Config.APP_NAME} - Análise de Commits por Repositório")

@st.cache_resource
def get_data_collector():
    return DataCollector()

collector = get_data_collector()

# Main controls in organized sections
st.header("⚙️ Controles do Sistema")

# Update button in full width for prominence
if st.button("🔄 Atualizar Todos os Repositórios (170 repos)", type="primary", use_container_width=True):
    try:
        # Create progress elements
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current: int, total: int, message: str):
            # Update progress bar
            progress = current / total if total > 0 else 0
            progress_bar.progress(progress)
            # Update status text
            status_text.markdown(f"**📈 {current}/{total}** - {message}")
            # Force UI update
            import time
            time.sleep(0.01)  # Very small delay
        
        # Start data collection with progress callback
        snapshot_id = collector.collect_all_data(progress_callback=update_progress)
        
        # Clear progress elements and show final result
        progress_bar.empty()
        status_text.empty()
        
        if snapshot_id:
            st.success(f"✅ Dados atualizados! Snapshot: {snapshot_id}")
            st.rerun()
        else:
            st.error("❌ Erro na atualização")
            
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")

st.divider()

# Filters in organized layout
st.subheader("📊 Filtros de Análise")

# First row: Snapshot and Repository type
col1, col2 = st.columns([3, 1])

with col1:
    # Snapshot selection - always show latest by default
    snapshots = collector.get_snapshots_summary()
    if snapshots:
        # Create snapshot options for selectbox
        snapshot_options = []
        snapshot_mapping = {}
        
        for i, snapshot in enumerate(snapshots):
            display_name = f"{snapshot['snapshot_id']} ({snapshot['timestamp']})"
            snapshot_options.append(display_name)
            snapshot_mapping[display_name] = snapshot['snapshot_id']
        
        # Always default to the first (latest) snapshot
        selected_snapshot_display = st.selectbox(
            "📸 Selecionar Snapshot:",
            options=snapshot_options,
            index=0,
            key="snapshot_selector"
        )
        
        snapshot_id = snapshot_mapping[selected_snapshot_display]
        
        # Display current snapshot info
        current_snapshot = next(s for s in snapshots if s['snapshot_id'] == snapshot_id)
        st.info(f"📊 {current_snapshot['repositories_count']} repos, {current_snapshot['commits_count']} commits, {current_snapshot['pull_requests_count']} PRs")
        
    else:
        st.warning("⚠️ Nenhum snapshot disponível. Clique em 'Atualizar' acima para criar o primeiro.")
        snapshot_id = None

with col2:
    # Filtro: Tipo de repositório
    filtro_tipo = st.selectbox(
        "🏢 Tipo",
        ("Todos", "INTERNO", "PUBLICO")
    )

# Second row: Date filters
st.write("**📅 Período de Análise**")
col3, col4, col5 = st.columns(3)

with col3:
    default_start_date = datetime.date(2025, 5, 5)
    start_date = st.date_input("Data Inicial", value=default_start_date)

with col4:
    default_end_date = datetime.date(2025, 5, 17)
    end_date = st.date_input("Data Final", value=default_end_date)

with col5:
    end_time = st.time_input("Hora Limite", value=datetime.time(3, 15, 0))

start_datetime = f"{start_date} 00:00:00"
end_datetime = f"{end_date} {end_time}"

# Configuration info
with st.expander("ℹ️ Configuração do Sistema"):
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Repositórios Configurados", len(Config.get_all_repositories()))
    with col_info2:
        st.metric("Repositórios Internos", len(Config.INTERNAL_REPOSITORIES))
    with col_info3:
        st.metric("Repositórios Públicos", len(Config.PUBLIC_REPOSITORIES))

if not snapshot_id:
    st.warning("⚠️ Nenhum snapshot selecionado. Use o botão 'Atualizar' acima para coletar dados.")
    st.stop()

# Load data from selected snapshot
try:
    data = collector.load_snapshot(snapshot_id)
    if not data or 'commits' not in data:
        st.error("❌ Não foi possível carregar os dados do snapshot selecionado.")
        st.stop()
except Exception as e:
    st.error(f"❌ Erro ao carregar snapshot: {str(e)}")
    st.stop()


# Get commits data
df_commits = data['commits']

# Apply repository type filter
if filtro_tipo == "INTERNO":
    df_commits = df_commits[df_commits['repo_name'].str.contains('-INTERNO', na=False)]
elif filtro_tipo == "PUBLICO":
    df_commits = df_commits[df_commits['repo_name'].str.contains('-PUBLICO', na=False)]
else:
    df_commits = df_commits[
        (df_commits['repo_name'].str.contains('-INTERNO', na=False)) |
        (df_commits['repo_name'].str.contains('-PUBLICO', na=False))
    ]

repositorios = df_commits['repo_name'].unique().tolist()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "❌ Repositórios SEM commits na janela",
    "⚠️ Repositórios SEM commits na janela MAS COM commits após",
    "🔍 Detalhar commits por projeto"
])

# Convert date column to datetime and handle timezone issues
df_commits['date_dt'] = pd.to_datetime(df_commits['date'], errors='coerce', utc=True)
start_dt = pd.to_datetime(start_datetime, utc=True)
end_dt = pd.to_datetime(end_datetime, utc=True)

# Exclude unwanted authors
excluded_authors = ['Inteli Hub', 'José Romualdo']
df_commits_filtered = df_commits[~df_commits['author'].isin(excluded_authors)]

registros_sem_janela = []
registros_sem_janela_com_apos = []

for repo in repositorios:
    repo_commits = df_commits_filtered[df_commits_filtered['repo_name'] == repo]
    
    # Check commits in the time window
    commits_na_janela = len(repo_commits[
        (repo_commits['date_dt'] >= start_dt) & 
        (repo_commits['date_dt'] <= end_dt)
    ])
    
    if commits_na_janela == 0:
        # Get authors for this repo
        authors_list = repo_commits['author'].unique().tolist()
        authors_str = ", ".join(authors_list) if authors_list else "Nenhum author registrado"
        
        registros_sem_janela.append({
            'Repositório': repo,
            'Commits na Janela?': 'Não',
            'Authors': authors_str
        })
        
        # Check commits after the window
        commits_apos = len(repo_commits[repo_commits['date_dt'] > end_dt])
        
        if commits_apos > 0:
            authors_apos = repo_commits[repo_commits['date_dt'] > end_dt]['author'].unique().tolist()
            authors_str_apos = ", ".join(authors_apos) if authors_apos else "Nenhum author registrado"
            
            registros_sem_janela_com_apos.append({
                'Repositório': repo,
                'Commits após a Janela': commits_apos,
                'Authors': authors_str_apos
            })

# TAB 1 - Overview
with tab1:
    st.header("📊 Visão Geral dos Dados")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    commits_na_janela_total = len(df_commits_filtered[
        (df_commits_filtered['date_dt'] >= start_dt) & 
        (df_commits_filtered['date_dt'] <= end_dt)
    ])
    
    with col1:
        st.metric("Repositórios Analisados", len(repositorios))
    
    with col2:
        st.metric("Total de Commits", len(df_commits_filtered))
    
    with col3:
        st.metric("Commits na Janela", commits_na_janela_total)
    
    with col4:
        st.metric("Snapshots Disponíveis", len(snapshots))
    
    st.divider()
    
    # Intelligent analysis
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Distribuição de Atividade")
        
        # Activity buckets
        activity_buckets = {"Sem commits": 0, "1-5 commits": 0, "6-15 commits": 0, "16+ commits": 0}
        
        for repo in repositorios:
            repo_commits = df_commits_filtered[df_commits_filtered['repo_name'] == repo]
            commits_count = len(repo_commits[
                (repo_commits['date_dt'] >= start_dt) & 
                (repo_commits['date_dt'] <= end_dt)
            ])
            
            if commits_count == 0:
                activity_buckets["Sem commits"] += 1
            elif commits_count <= 5:
                activity_buckets["1-5 commits"] += 1
            elif commits_count <= 15:
                activity_buckets["6-15 commits"] += 1
            else:
                activity_buckets["16+ commits"] += 1
        
        # Create pie chart data
        activity_df = pd.DataFrame(list(activity_buckets.items()), columns=['Categoria', 'Quantidade'])
        
        if not activity_df.empty and activity_df['Quantidade'].sum() > 0:
            # Color coding
            colors = {"Sem commits": "🔴", "1-5 commits": "🟡", "6-15 commits": "🟢", "16+ commits": "🔵"}
            for _, row in activity_df.iterrows():
                emoji = colors.get(row['Categoria'], '⚪')
                st.write(f"{emoji} **{row['Categoria']}**: {row['Quantidade']} repositórios")
    
    with col_right:
        st.subheader("📅 Atividade por Track")
        
        # Group by track
        track_activity = {"T01 (CC)": 0, "T02 (EC)": 0, "T03 (SI)": 0}
        
        for repo in repositorios:
            repo_commits = df_commits_filtered[df_commits_filtered['repo_name'] == repo]
            commits_count = len(repo_commits[
                (repo_commits['date_dt'] >= start_dt) & 
                (repo_commits['date_dt'] <= end_dt)
            ])
            
            if "T01" in repo:
                track_activity["T01 (CC)"] += commits_count
            elif "T02" in repo:
                track_activity["T02 (EC)"] += commits_count
            elif "T03" in repo:
                track_activity["T03 (SI)"] += commits_count
        
        # Display track metrics
        for track, commits in track_activity.items():
            st.metric(track, f"{commits} commits")
    
    st.divider()
    
    # Timeline analysis
    st.subheader("📊 Evolução dos Commits na Janela")
    
    # Group commits by day in the window
    commits_in_window = df_commits_filtered[
        (df_commits_filtered['date_dt'] >= start_dt) & 
        (df_commits_filtered['date_dt'] <= end_dt)
    ].copy()
    
    if not commits_in_window.empty:
        commits_in_window['dia'] = commits_in_window['date_dt'].dt.date
        daily_commits = commits_in_window.groupby('dia').size().reset_index()
        daily_commits.columns = ['Data', 'Commits']
        
        st.line_chart(daily_commits.set_index('Data'))
        
        # Show top authors
        st.subheader("🏆 Top 10 Autores na Janela")
        if not commits_in_window.empty:
            top_authors = commits_in_window['author'].value_counts().head(10)
            
            # Create a DataFrame for better formatting
            authors_df = pd.DataFrame({
                'Autor': top_authors.index,
                'Commits': top_authors.values
            })
            
            # Display as chart
            import plotly.express as px
            fig = px.bar(authors_df, x='Autor', y='Commits', 
                        title="Top 10 Autores por Número de Commits")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum commit encontrado na janela selecionada.")

# TAB 2 - SEM commits na janela
with tab2:
    st.header("Repositórios SEM commits na janela selecionada")
    df_sem_janela = pd.DataFrame(registros_sem_janela)
    if not df_sem_janela.empty:
        st.dataframe(df_sem_janela, use_container_width=True)
        st.error(f"{len(df_sem_janela)} repositórios NÃO fizeram commits na janela.")
    else:
        st.success("Todos os repositórios realizaram commits na janela selecionada!")

# TAB 3 - SEM commits na janela MAS COM commits após
with tab3:
    st.header("Repositórios SEM commits na janela MAS COM commits após a janela")
    df_sem_janela_com_apos = pd.DataFrame(registros_sem_janela_com_apos)
    if not df_sem_janela_com_apos.empty:
        st.dataframe(df_sem_janela_com_apos, use_container_width=True)
        st.warning(f"{len(df_sem_janela_com_apos)} repositórios NÃO fizeram commits na janela mas fizeram APÓS.")
    else:
        st.success("Nenhum repositório fez commit após a janela sem ter feito na janela!")

# TAB 4 - Detalhamento por projeto
with tab4:
    st.header("Detalhamento de commits por repositório")

    if repositorios:
        selected_repo = st.selectbox("Selecione o repositório para detalhar", repositorios, key="repo_select")

        # Get detailed commits for selected repo
        df_detalhe = df_commits_filtered[
            df_commits_filtered['repo_name'] == selected_repo
        ][['author', 'date', 'message']].sort_values('date')

        if not df_detalhe.empty:
            st.dataframe(df_detalhe, use_container_width=True)
            st.success(f"Total de {len(df_detalhe)} commits encontrados para {selected_repo}.")

            # Group commits by day
            repo_commits_detail = df_commits_filtered[df_commits_filtered['repo_name'] == selected_repo].copy()
            repo_commits_detail['dia'] = pd.to_datetime(repo_commits_detail['date'], utc=True).dt.date
            df_agrupada = repo_commits_detail.groupby('dia').size().reset_index()
            df_agrupada.columns = ['dia', 'total_commits']

            if not df_agrupada.empty:
                st.subheader("📈 Commits por dia")
                
                # Use plotly for better visualization
                import plotly.express as px
                fig = px.bar(df_agrupada, x='dia', y='total_commits', 
                            title=f"Commits por dia - {selected_repo}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Nenhum commit encontrado para gerar gráfico.")
        else:
            st.warning(f"Nenhum commit encontrado para {selected_repo}.")
    else:
        st.info("Nenhum repositório encontrado para o filtro atual.")