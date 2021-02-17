import pandas as pd
import numpy as np
import sys
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar 
import geopandas as gpd
from matplotlib import pyplot as plt
plt.ioff()

#from government intervetions google drive file, errors showing 2019 in index 33 changed to 2020
#filter values were changed so Namibia could be read
df_cat_gov_int = pd.read_csv('government interventions - measures-small.csv', keep_default_na=False, na_values=['']) 
#to make the dates datetime datatypes
df_cat_gov_int.date = df_cat_gov_int.date.apply(lambda x: pd.Timestamp(x, unit='D')) 

# csv made from values taken from https://www.worldatlas.com/aatlas/ctycodes.html, EU was manually added
# NA is Namibia, so the filter is set to false 
df_country_codes = pd.read_csv('Country_Codes.csv',na_filter = False)  

#drop rows where there the country isn't known or actions aren't taken 
df_cgi_drop = df_cat_gov_int.dropna(subset=['actions/0/name','adm/0']) 

#Keeping only columns that may be used, index is reset, but original index has the column name 'old_index'
df_clean = df_cgi_drop[['adm/0',
 'date',
 'schools_closed',
 'traveller_quarantine',
 'border_control',
 'closure_leisureandbars',
 'lockdown',
 'home_office',
 'primary_residence',
 'test_limitations']].reset_index().rename(columns={'index':'old_index'})

#all actions
actions = ['schools_closed',
 'traveller_quarantine',
 'border_control',
 'closure_leisureandbars',
 'lockdown',
 'home_office',
 'primary_residence',
 'test_limitations']

actionscap = ['Schools Closed',
 'Traveller Quarantine',
 'Border Control',
 'Closure Leisure and Bars',
 'Lockdown',
 'Home Office',
 'Primary Residence',
 'Test Limitations']

#country codes used in the loops below
country_codes = df_clean['adm/0'].tolist()

#start dates for each country for each action
start_dates = []
country_list = []

for j in country_codes:
    if j in country_list:
        continue
    else:
        for i in actions:
            #see if action is done
            check = (df_clean[df_clean['adm/0']==j].sort_values(by='date')[i].cumsum() == 1).values.any()
            if check == False:
                start_dates.append(np.datetime64('NaT'))
            else:
                #getting dates actions started
                start_date = df_clean.iloc[(df_clean[df_clean['adm/0']==j].sort_values(by='date')[i].cumsum() == 1).idxmax()].date 
                start_dates.append(start_date)          
               
        country_list.append(j)

#this is a dataframe with each country and start date for actions taken 
df = pd.DataFrame([start_dates[i:i+8] for i in range(0,len(start_dates),8)], columns = actionscap, index = country_list).reset_index().rename(columns={'index':'cc_index'})

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

#Plots schools_closed start dates for each country 
class Window(QDialog): 
       
    def __init__(self, parent=None): 
        super(Window, self).__init__(parent) 
    
        self.figure = Figure()  
        self.canvas = FigureCanvas(self.figure) 
        self.toolbar = NavigationToolbar(self.canvas, self) 
        self.button = QPushButton('Plot') 
        self.button.clicked.connect(self.plot_maps) 
        self.cb = QComboBox()
        self.cb.addItems(actionscap)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.cb)
        hlayout.addWidget(self.button)
        layout = QVBoxLayout() 
        layout.addWidget(self.toolbar) 
        layout.addWidget(self.canvas) 
        layout.addLayout(hlayout) 
        self.setLayout(layout) 

    def plot_maps(self):

        self.figure.clear() 
        ax = self.figure.add_subplot(111)
        nnl = np.argwhere((df[f'{self.cb.currentText()}'].notnull() == True).to_numpy()).transpose().tolist()[0]
        yp = df.iloc[nnl].sort_values(by='cc_index').reset_index()['cc_index'] 
        df_yp = pd.DataFrame(yp.values, columns = ['yp'])
        df_yp_c = df_yp.join(df_country_codes.set_index('A2 (ISO)'), on='yp')
        months = pd.Series([int(df.iloc[nnl].sort_values(by = 'cc_index')[f'{self.cb.currentText()}'][i].month) for i in df.iloc[nnl].sort_values(by = 'cc_index')[f'{self.cb.currentText()}'].index])
        monthdic = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov',12:'Dec', 13:'NaN'}
        df_tomerge = df_yp_c.rename(columns = {'A3 (UN)':'iso_a3'})
        df_tomerge['Months'] = months.values    
        dfgp_tomerge = gpd.GeoDataFrame(df_tomerge)
        df2 = world.merge(dfgp_tomerge,  on = 'iso_a3' ,how = 'left')
        df2.plot(column = 'Months', categorical = True, legend = True, missing_kwds={'color': 'lightgrey'}, ax = ax)

        def replace_legend_items(legend, mapping):
            for txt in legend.get_texts():
                for k,v in mapping.items():
                    if txt.get_text() == str(float(k)):
                        txt.set_text(v)

        replace_legend_items(ax.get_legend(), monthdic)
        ax.set_title('Month Started ' + self.cb.currentText())
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()     



    
if __name__ == '__main__': 
       
    app = QApplication(sys.argv)  
    main = Window() 
    main.show() 
    sys.exit(app.exec_()) 
