mode(-1)
R = csvRead("./input_data.log"," ")

[T,N] = size(R)

T = min(7000, T)

t = [1:T]'

position = 0.617 * (R(t,3) - 512) / 1024
voltage = R(t,2)


clf
plot2d(t, voltage , style=2)
plot2d(t, position, style=5)

D = [t,voltage,position]

csvWrite(D, "./input_data_formatted.log", " ")
