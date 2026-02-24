import plotly.graph_objects as go


def event_display(hits_set, cluster_label=[], E=[]):

    hits_x = hits_set[:,0]
    hits_y = hits_set[:,1]
    hits_z = hits_set[:,2]
    hits_c = hits_set[:,3]

    # --------------------------------------------------
    # Cube dimensions
    # --------------------------------------------------
    Lmin, Lmax = -70, 70

    TPC_x_min, TPC_x_max = 3.07, 63.931
    TPC_z_min, TPC_z_max = 2.68, 64.3161
    TPC_y_min, TPC_y_max = -61.85, 61.85 

    # --------------------------------------------------
    # Create event display
    # --------------------------------------------------
    symbol_li = ['circle', 'circle-open', 'cross', 'diamond', 'diamond-open', 'square', 'square-open', 'x']
    fig = go.Figure()

    if not len(E):
        if not len(cluster_label):
            # --- Add hit points colored by time ---
            fig.add_trace(go.Scatter3d(
                x=hits_x, y=hits_y, z=hits_z,
                mode='markers',
                marker=dict(
                    size=4,
                    color=hits_c,             # <-- color by time
                    colorscale='Turbo',      # 'Viridis', 'Plasma', 'Turbo', etc.
                    colorbar=dict(title="Time"),
                    opacity=0.9
                ),
                name="Hits"
            ))
        else:
            # --- Add hit points with different labels for different clusters and colored by time ---
            for index,i in enumerate(set(cluster_label)):
                fig.add_trace(go.Scatter3d(
                    x=hits_x[cluster_label==i], y=hits_y[cluster_label==i], z=hits_z[cluster_label==i],
                    mode='markers',
                    marker=dict(
                        size=4,
                        color=hits_c[cluster_label==i],             # <-- color by time
                        colorscale='Turbo',      # 'Viridis', 'Plasma', 'Turbo', etc.
                        colorbar=dict(title="Time"),
                        opacity=0.9,
                        symbol=symbol_li[index%len(set(symbol_li))],
                        name=f"Cluster Label: {i}"
                    ),
                    name=f'Cluster Label: {i}'
                ))
    elif len(E):
        if not len(cluster_label):
            # --- Add hit points colored by energy ---
            fig.add_trace(go.Scatter3d(
                x=hits_x, y=hits_y, z=hits_z,
                mode='markers',
                marker=dict(
                    size=4,
                    color=E,             # <-- color by time
                    colorscale='Viridis',      # 'Viridis', 'Plasma', 'Turbo', etc.
                    colorbar=dict(title="Energy (MeV)"),
                    opacity=0.9
                ),
                name="Hits"
            ))
        else:
            # --- Add hit points with different labels for different clusters and colored by energy ---
            for index,i in enumerate(set(cluster_label)):
                fig.add_trace(go.Scatter3d(
                    x=hits_x[cluster_label==i], y=hits_y[cluster_label==i], z=hits_z[cluster_label==i],
                    mode='markers',
                    marker=dict(
                        size=4,
                        color=E,             # <-- color by time
                        colorscale='Viridis',      # 'Viridis', 'Plasma', 'Turbo', etc.
                        colorbar=dict(title="Energy (MeV)"),
                        opacity=0.9,
                        symbol=symbol_li[index%len(set(symbol_li))]
                    ),
                    name=f'Cluster Label: {i}'
                ))

    # --------------------------------------------------
    # Add detector cube edges
    # --------------------------------------------------
    cube_edges = [
        # bottom
        [(Lmin,Lmin,Lmin), (Lmax,Lmin,Lmin)],
        [(Lmax,Lmin,Lmin), (Lmax,Lmax,Lmin)],
        [(Lmax,Lmax,Lmin), (Lmin,Lmax,Lmin)],
        [(Lmin,Lmax,Lmin), (Lmin,Lmin,Lmin)],

        # top
        [(Lmin,Lmin,Lmax), (Lmax,Lmin,Lmax)],
        [(Lmax,Lmin,Lmax), (Lmax,Lmax,Lmax)],
        [(Lmax,Lmax,Lmax), (Lmin,Lmax,Lmax)],
        [(Lmin,Lmax,Lmax), (Lmin,Lmin,Lmax)],

        # verticals
        [(Lmin,Lmin,Lmin), (Lmin,Lmin,Lmax)],
        [(Lmax,Lmin,Lmin), (Lmax,Lmin,Lmax)],
        [(Lmax,Lmax,Lmin), (Lmax,Lmax,Lmax)],
        [(Lmin,Lmax,Lmin), (Lmin,Lmax,Lmax)],
    ]


    m0_edges = [
            # bottom
        [(TPC_x_min,TPC_y_min,TPC_z_min), (TPC_x_max,TPC_y_min,TPC_z_min)],
        [(TPC_x_max,TPC_y_min,TPC_z_min), (TPC_x_max,TPC_y_max,TPC_z_min)],
        [(TPC_x_max,TPC_y_max,TPC_z_min), (TPC_x_min,TPC_y_max,TPC_z_min)],
        [(TPC_x_min,TPC_y_max,TPC_z_min), (TPC_x_min,TPC_y_min,TPC_z_min)],

        # top
        [(TPC_x_min,TPC_y_min,TPC_z_max), (TPC_x_max,TPC_y_min,TPC_z_max)],
        [(TPC_x_max,TPC_y_min,TPC_z_max), (TPC_x_max,TPC_y_max,TPC_z_max)],
        [(TPC_x_max,TPC_y_max,TPC_z_max), (TPC_x_min,TPC_y_max,TPC_z_max)],
        [(TPC_x_min,TPC_y_max,TPC_z_max), (TPC_x_min,TPC_y_min,TPC_z_max)],

        # verticals
        [(TPC_x_min,TPC_y_min,TPC_z_min), (TPC_x_min,TPC_y_min,TPC_z_max)],
        [(TPC_x_max,TPC_y_min,TPC_z_min), (TPC_x_max,TPC_y_min,TPC_z_max)],
        [(TPC_x_max,TPC_y_max,TPC_z_min), (TPC_x_max,TPC_y_max,TPC_z_max)],
        [(TPC_x_min,TPC_y_max,TPC_z_min), (TPC_x_min,TPC_y_max,TPC_z_max)],

    ]

    m1_edges = [
            # bottom
        [(-1*TPC_x_min,TPC_y_min,TPC_z_min), (-1*TPC_x_max,TPC_y_min,TPC_z_min)],
        [(-1*TPC_x_max,TPC_y_min,TPC_z_min), (-1*TPC_x_max,TPC_y_max,TPC_z_min)],
        [(-1*TPC_x_max,TPC_y_max,TPC_z_min), (-1*TPC_x_min,TPC_y_max,TPC_z_min)],
        [(-1*TPC_x_min,TPC_y_max,TPC_z_min), (-1*TPC_x_min,TPC_y_min,TPC_z_min)],

        # top
        [(-1*TPC_x_min,TPC_y_min,TPC_z_max), (-1*TPC_x_max,TPC_y_min,TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_min,TPC_z_max), (-1*TPC_x_max,TPC_y_max,TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_max,TPC_z_max), (-1*TPC_x_min,TPC_y_max,TPC_z_max)],
        [(-1*TPC_x_min,TPC_y_max,TPC_z_max), (-1*TPC_x_min,TPC_y_min,TPC_z_max)],

        # verticals
        [(-1*TPC_x_min,TPC_y_min,TPC_z_min), (-1*TPC_x_min,TPC_y_min,TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_min,TPC_z_min), (-1*TPC_x_max,TPC_y_min,TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_max,TPC_z_min), (-1*TPC_x_max,TPC_y_max,TPC_z_max)],
        [(-1*TPC_x_min,TPC_y_max,TPC_z_min), (-1*TPC_x_min,TPC_y_max,TPC_z_max)],

    ]


    m2_edges = [
            # bottom
        [(TPC_x_min,TPC_y_min,-1*TPC_z_min), (TPC_x_max,TPC_y_min,-1*TPC_z_min)],
        [(TPC_x_max,TPC_y_min,-1*TPC_z_min), (TPC_x_max,TPC_y_max,-1*TPC_z_min)],
        [(TPC_x_max,TPC_y_max,-1*TPC_z_min), (TPC_x_min,TPC_y_max,-1*TPC_z_min)],
        [(TPC_x_min,TPC_y_max,-1*TPC_z_min), (TPC_x_min,TPC_y_min,-1*TPC_z_min)],

        # top
        [(TPC_x_min,TPC_y_min,-1*TPC_z_max), (TPC_x_max,TPC_y_min,-1*TPC_z_max)],
        [(TPC_x_max,TPC_y_min,-1*TPC_z_max), (TPC_x_max,TPC_y_max,-1*TPC_z_max)],
        [(TPC_x_max,TPC_y_max,-1*TPC_z_max), (TPC_x_min,TPC_y_max,-1*TPC_z_max)],
        [(TPC_x_min,TPC_y_max,-1*TPC_z_max), (TPC_x_min,TPC_y_min,-1*TPC_z_max)],

        # verticals
        [(TPC_x_min,TPC_y_min,-1*TPC_z_min), (TPC_x_min,TPC_y_min,-1*TPC_z_max)],
        [(TPC_x_max,TPC_y_min,-1*TPC_z_min), (TPC_x_max,TPC_y_min,-1*TPC_z_max)],
        [(TPC_x_max,TPC_y_max,-1*TPC_z_min), (TPC_x_max,TPC_y_max,-1*TPC_z_max)],
        [(TPC_x_min,TPC_y_max,-1*TPC_z_min), (TPC_x_min,TPC_y_max,-1*TPC_z_max)],

    ]


    m3_edges = [
            # bottom
        [(-1*TPC_x_min,TPC_y_min,-1*TPC_z_min), (-1*TPC_x_max,TPC_y_min,-1*TPC_z_min)],
        [(-1*TPC_x_max,TPC_y_min,-1*TPC_z_min), (-1*TPC_x_max,TPC_y_max,-1*TPC_z_min)],
        [(-1*TPC_x_max,TPC_y_max,-1*TPC_z_min), (-1*TPC_x_min,TPC_y_max,-1*TPC_z_min)],
        [(-1*TPC_x_min,TPC_y_max,-1*TPC_z_min), (-1*TPC_x_min,TPC_y_min,-1*TPC_z_min)],

        # top
        [(-1*TPC_x_min,TPC_y_min,-1*TPC_z_max), (-1*TPC_x_max,TPC_y_min,-1*TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_min,-1*TPC_z_max), (-1*TPC_x_max,TPC_y_max,-1*TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_max,-1*TPC_z_max), (-1*TPC_x_min,TPC_y_max,-1*TPC_z_max)],
        [(-1*TPC_x_min,TPC_y_max,-1*TPC_z_max), (-1*TPC_x_min,TPC_y_min,-1*TPC_z_max)],

        # verticals
        [(-1*TPC_x_min,TPC_y_min,-1*TPC_z_min), (-1*TPC_x_min,TPC_y_min,-1*TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_min,-1*TPC_z_min), (-1*TPC_x_max,TPC_y_min,-1*TPC_z_max)],
        [(-1*TPC_x_max,TPC_y_max,-1*TPC_z_min), (-1*TPC_x_max,TPC_y_max,-1*TPC_z_max)],
        [(-1*TPC_x_min,TPC_y_max,-1*TPC_z_min), (-1*TPC_x_min,TPC_y_max,-1*TPC_z_max)],

    ]

    for (x0,y0,z0),(x1,y1,z1) in cube_edges:
        fig.add_trace(go.Scatter3d(
            x=[x0,x1],
            y=[y0,y1],
            z=[z0,z1],
            mode='lines',
            line=dict(color='black', width=4),
            showlegend=False
        ))


    for (x0,y0,z0),(x1,y1,z1) in m0_edges:
        fig.add_trace(go.Scatter3d(
            x=[x0,x1],
            y=[y0,y1],
            z=[z0,z1],
            mode='lines',
            line=dict(color='black', width=4),
            showlegend=False
        ))

    for (x0,y0,z0),(x1,y1,z1) in m1_edges:
        fig.add_trace(go.Scatter3d(
            x=[x0,x1],
            y=[y0,y1],
            z=[z0,z1],
            mode='lines',
            line=dict(color='black', width=4),
            showlegend=False
        ))

    for (x0,y0,z0),(x1,y1,z1) in m2_edges:
        fig.add_trace(go.Scatter3d(
            x=[x0,x1],
            y=[y0,y1],
            z=[z0,z1],
            mode='lines',
            line=dict(color='black', width=4),
            showlegend=False
        ))

    for (x0,y0,z0),(x1,y1,z1) in m3_edges:
        fig.add_trace(go.Scatter3d(
            x=[x0,x1],
            y=[y0,y1],
            z=[z0,z1],
            mode='lines',
            line=dict(color='black', width=4),
            showlegend=False
        ))   

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='x [cm]', range=[Lmin, Lmax]),
            yaxis=dict(title='y [cm]', range=[Lmin, Lmax]),
            zaxis=dict(title='z [cm]', range=[Lmin, Lmax]),
            aspectmode='cube'
        ),
        scene_camera=dict(
        up=dict(x=0, y=1, z=0),  # Defines which direction is 'up', in this case it should be y
        ),
        width=800,
        height=800,
        title="2x2 Event Display",
        legend=dict(
            xanchor='left',
            yanchor='bottom'
        )
    )

    fig.show()