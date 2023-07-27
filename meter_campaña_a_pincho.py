# Ruta para el formulario de selección de tabla
@app.route('/meter_a_pincho', methods=['GET', 'POST'])
def seleccionar_tabla():
    # Crear una nueva campaña
    new_campaign = Campaigns(
        Campaign_title='Mi nueva campaña',
        BeginDate='2023-07-25',
        EndDate='2023-08-31',
        Status=True
    )
    # Agregar la nueva campaña a la base de datos
    db.session.add(new_campaign)
    db.session.commit()

    return "Datos de Campaigns almacenados correctamente"
