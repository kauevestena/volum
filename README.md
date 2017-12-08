# volumator
Repositorio do Plugin para QGIS de calculo de volumes para um conjunto esparso de dados

Há uma boa quantidade de ferramentas para calculo de Volumes em Estruturas Raster, geralmente voltadas para levantamentos em grande ou média escala

O Volumator foi projetado para o calculo de volumes para um conjunto vetorial esparso de dados, na forma de pontos XYZ, tal qual o exemplo mostrado abaixo (uma malha de 12 pontos coletados por técnicas topográficas)

                        ----------------------------
                            ID,X,Y,Z
                            A0,1000,1000,999.958
                            A1,1010,1000,999.435
                            A2,1020,1000,998.579
                            A3,1030,1000,997.48
                            B0,1000,1010,1000.148
                            B1,1010,1010,999.566
                            B2,1020,1010,998.777
                            B3,1030,1010,997.478
                            C0,1000,1020,1000.297
                            C1,1010,1020,999.476
                            C2,1020,1020,999.017
                            C3,1030,1020,997.567
                            D0,1000,1030,1000.228
                            D1,1010,1030,999.645
                            D2,1020,1030,999.291
                            D3,1030,1030,997.815
                        ----------------------------

O arquivo de entrada deve OBRIGATÓRIAMENTE conter o cabeçalho no seguinte formato:
ID,X,Y,Z
Com esses Exatos 4 campos, sendo um ID dado pelo usuario e as coordenadas do ponto

Há um campo para seleção do CRS dos dados, com a opção do CRS ortografico, que possui a métrica de um plano topográfico, caso o Topocentro seja o ponto de tangencia e a extensao nao exceda ~30 Km a partir deste

O calculo é feito com base em uma altitude fornecida no campo de entrada disponível na janela do plugin

Há um botao para obter os valores máximo e mínimo de Altitude (ou "cota"), uma vez que acima do primeiro se terá apenas volume de aterro e abaixo do minímo se terá apenas volume de corte.

Para qualquer altitude intermediária, será gerada a curva de nivel desta, havendo a possibilidade de gerar a planilha de locação de tal curva, no intervalo especificado. Caso o ID de um dos pontos contenha: "EST","est","Est", tal ponto será automaticamente selecionado como ponto para instalacao. O mesmo vale para "ORI","ori","Ori","RE","Re","re", que sera automaticamente selecionado como ponto para orientação.
 