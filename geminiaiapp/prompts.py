try_on_prompt=(
        """
        TASK: MULTI-IMAGE COMPOSITION / VIRTUAL TRY-ON
        1. Take the dress/pants design, including all intricate details, fabrics, and styling, from Image 2.
        2. Apply this exact dress onto the person seen in Image 1.
        3. Maintain the precise pose, body orientation, and expression of the person from Image 1.
        4. Ensure the fabric fits naturally, draping realistically over the pose, respecting proportions.
        5. Create an elegant, professional studio background color that complements the dress.
        6. Generate the FULL body of the person from head to toe, do not crop any body part.


        ### MAKE SURE IT LOOKS REALISTIC
        """
    )