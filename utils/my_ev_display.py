import plotly.graph_objects as go


def event_display(
    hits_set,
    *,
    fig=None,
    trace_name="Hits",
    title="2x2 Event Display",
    colorbar_title="Time",
    colorscale="Turbo",
    marker_kwargs=None,
    show=True,
    return_fig=False,
):

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
    if fig is None:
        fig = go.Figure()

    marker = dict(
        size=4,
        color=hits_c,
        colorscale=colorscale,
        colorbar=dict(title=colorbar_title),
        opacity=0.9
    )
    if marker_kwargs is not None:
        marker.update(marker_kwargs)

    # --- Add hit points colored by time ---
    fig.add_trace(go.Scatter3d(
        x=hits_x, y=hits_y, z=hits_z,
        mode='markers',
        marker=marker,
        name=trace_name
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
        width=800,
        height=800,
        title=title
    )

    if show:
        fig.show()

    if return_fig:
        return fig
