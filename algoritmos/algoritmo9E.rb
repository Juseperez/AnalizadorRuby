class Persona
  @species = "Homo sapiens"

  def initialize(name)
    @name = name
  end

  def saludar
    puts "Hola, #{@name}"
  end
end