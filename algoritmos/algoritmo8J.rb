MI_CONSTANTE = 10
MI_CONSTANTE = 20  # Esto generará advertencia
x = 10

# ERROR: break fuera de bucle
break

if x > 5
    # ERROR: next fuera de bucle (solo válido dentro de for/while)
    next
end

# Bucle válido
while x > 0
    puts x
    x -= 1

    if x == 5
        break   # ✔️ break válido
    end
end

# ERROR: next fuera de bucle
next

for i in 1..3
    puts i
    if i == 2
        next   # ✔️ next válido
    end
end

# ERROR: break fuera de estructura iterativa
break
