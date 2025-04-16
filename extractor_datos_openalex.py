"""
Extracción de Datos de Publicaciones Científicas Ecuatorianas
Autor: Dirección de Productos y Servicios de CEDIA
Desarrollado por: Freddy Sumba

Este script extrae y analiza datos de publicaciones científicas ecuatorianas
utilizando la API de OpenAlex, generando visualizaciones y análisis estadísticos
sobre el estado de la ciencia abierta en Ecuador.
"""

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import numpy as np

# Configuración de colores corporativos de CEDIA
CEDIA_COLORS = {
    'dark_blue': '#1D3A54',
    'turquoise': '#4FBCCC',
    'medium_blue': '#2A4C8C',
    'light_blue': '#3866CA',
    'green': '#8CC63F',
    'orange': '#F7941D'
}

# Configuración de directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'datos')
VIZ_DIR = os.path.join(BASE_DIR, 'visualizaciones')

# Crear directorios si no existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VIZ_DIR, exist_ok=True)

# Configuración de estilo para visualizaciones
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.labelcolor'] = CEDIA_COLORS['dark_blue']
plt.rcParams['axes.titlecolor'] = CEDIA_COLORS['dark_blue']
plt.rcParams['xtick.color'] = CEDIA_COLORS['dark_blue']
plt.rcParams['ytick.color'] = CEDIA_COLORS['dark_blue']

class OpenAlexExtractor:
    """Clase para extraer y analizar datos de OpenAlex"""
    
    def __init__(self, email='freddy.sumba@cedia.org.ec'):
        """
        Inicializa el extractor con el email para identificación en la API
        
        Args:
            email (str): Email para identificación en la API de OpenAlex
        """
        self.email = email
        self.base_url = 'https://api.openalex.org'
        
        # Calcular período de análisis (últimos 5 años)
        self.current_year = datetime.now().year
        self.five_years_ago = self.current_year - 5
        self.period = f"{self.five_years_ago}-{self.current_year}"
        
        # Metadatos generales
        self.total_publications = 0
        
    def query_api(self, endpoint, params=None):
        """
        Consulta la API de OpenAlex
        
        Args:
            endpoint (str): Endpoint de la API (works, authors, etc.)
            params (dict): Parámetros de consulta
            
        Returns:
            dict: Respuesta JSON de la API
        """
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        
        # Añadir email para identificación
        params['mailto'] = self.email
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en la consulta: {response.status_code}")
            print(response.text)
            return None
    
    def get_general_stats(self):
        """
        Obtiene estadísticas generales de publicaciones ecuatorianas
        
        Returns:
            dict: Estadísticas generales
        """
        print("Obteniendo estadísticas generales...")
        
        # Consultar total de publicaciones
        params = {
            'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period}',
            'per_page': 1
        }
        
        results = self.query_api('works', params)
        if results and 'meta' in results:
            self.total_publications = results['meta']['count']
            
            # Guardar metadatos generales
            metadata = {
                'total_publicaciones': self.total_publications,
                'periodo': self.period,
                'fecha_consulta': datetime.now().strftime('%Y-%m-%d')
            }
            
            with open(os.path.join(DATA_DIR, 'metadatos_generales.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Total de publicaciones encontradas: {self.total_publications}")
            return metadata
        
        return None
    
    def get_oa_stats(self):
        """
        Obtiene estadísticas de acceso abierto
        
        Returns:
            dict: Estadísticas de acceso abierto
        """
        print("Analizando estadísticas de acceso abierto...")
        
        # Consultar publicaciones de acceso abierto
        params_oa = {
            'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period},is_oa:true',
            'per_page': 1
        }
        
        results_oa = self.query_api('works', params_oa)
        if results_oa and 'meta' in results_oa:
            total_oa = results_oa['meta']['count']
            percentage_oa = (total_oa / self.total_publications) * 100
            
            print(f"Publicaciones en acceso abierto: {total_oa} ({percentage_oa:.2f}%)")
            
            # Consultar distribución por tipo de acceso abierto
            params_oa_types = {
                'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period}',
                'group_by': 'oa_status'
            }
            
            results_oa_types = self.query_api('works', params_oa_types)
            if results_oa_types and 'group_by' in results_oa_types:
                oa_types_data = {}
                
                for item in results_oa_types['group_by']:
                    oa_type = item['key']
                    count = item['count']
                    percentage = (count / self.total_publications) * 100
                    
                    oa_types_data[oa_type] = {
                        'count': count,
                        'percentage': percentage
                    }
                    
                    print(f"  - {oa_type}: {count} ({percentage:.2f}%)")
                
                # Guardar datos de tipos de OA
                with open(os.path.join(DATA_DIR, 'datos_tipos_oa.json'), 'w') as f:
                    json.dump(oa_types_data, f, indent=2)
                
                # Crear visualización de tipos de OA
                self.visualize_oa_types(oa_types_data)
                
                return {
                    'total_oa': total_oa,
                    'percentage_oa': percentage_oa,
                    'oa_types': oa_types_data
                }
        
        return None
    
    def get_data_by_field(self):
        """
        Obtiene datos por áreas de conocimiento
        
        Returns:
            dict: Datos por áreas de conocimiento
        """
        print("Analizando datos por áreas de conocimiento...")
        
        # Definir las principales áreas de conocimiento
        areas_conocimiento = [
            {'id': 'https://openalex.org/C41008148', 'nombre': 'Computer science'},
            {'id': 'https://openalex.org/C86803240', 'nombre': 'Biology'},
            {'id': 'https://openalex.org/C185592680', 'nombre': 'Chemistry'},
            {'id': 'https://openalex.org/C127313418', 'nombre': 'Engineering'},
            {'id': 'https://openalex.org/C71924100', 'nombre': 'Medicine'},
            {'id': 'https://openalex.org/C33923547', 'nombre': 'Physics'},
            {'id': 'https://openalex.org/C144133560', 'nombre': 'Mathematics'},
            {'id': 'https://openalex.org/C162324750', 'nombre': 'Economics'},
            {'id': 'https://openalex.org/C17744445', 'nombre': 'Political science'},
            {'id': 'https://openalex.org/C138885662', 'nombre': 'Education'},
            {'id': 'https://openalex.org/C39432304', 'nombre': 'Environmental science'},
            {'id': 'https://openalex.org/C15744967', 'nombre': 'Psychology'},
            {'id': 'https://openalex.org/C121332964', 'nombre': 'Sociology'}
        ]
        
        # Consultar datos para cada área
        fields_data = {}
        for area in areas_conocimiento:
            area_id = area['id']
            area_nombre = area['nombre']
            
            # Consultar publicaciones para esta área
            params_area = {
                'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period},concepts.id:{area_id}',
                'per_page': 1
            }
            
            results_area = self.query_api('works', params_area)
            if results_area and 'meta' in results_area:
                count = results_area['meta']['count']
                percentage = (count / self.total_publications) * 100
                
                fields_data[area_id] = {
                    'nombre': area_nombre,
                    'publicaciones': count,
                    'porcentaje': percentage
                }
                
                print(f"  - {area_nombre}: {count} publicaciones ({percentage:.2f}%)")
                
                # Consultar datos de acceso abierto para esta área
                params_area_oa = {
                    'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period},concepts.id:{area_id},is_oa:true',
                    'per_page': 1
                }
                
                results_area_oa = self.query_api('works', params_area_oa)
                if results_area_oa and 'meta' in results_area_oa:
                    count_oa = results_area_oa['meta']['count']
                    percentage_oa = (count_oa / count) * 100
                    
                    fields_data[area_id]['publicaciones_oa'] = count_oa
                    fields_data[area_id]['porcentaje_oa'] = percentage_oa
                    
                    print(f"    - Acceso abierto: {count_oa} publicaciones ({percentage_oa:.2f}%)")
                    
                    # Consultar distribución por tipo de OA
                    params_area_oa_types = {
                        'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period},concepts.id:{area_id}',
                        'group_by': 'oa_status'
                    }
                    
                    results_area_oa_types = self.query_api('works', params_area_oa_types)
                    if results_area_oa_types and 'group_by' in results_area_oa_types:
                        oa_data = {}
                        for item in results_area_oa_types['group_by']:
                            oa_type = item['key']
                            oa_count = item['count']
                            oa_percentage = (oa_count / count) * 100
                            oa_data[oa_type] = {
                                'count': oa_count,
                                'percentage': oa_percentage
                            }
                        
                        fields_data[area_id]['oa_status'] = oa_data
        
        # Guardar datos por áreas
        with open(os.path.join(DATA_DIR, 'datos_por_areas.json'), 'w') as f:
            json.dump(fields_data, f, indent=2)
        
        # Crear visualizaciones
        self.visualize_fields_data(fields_data)
        
        return fields_data
    
    def get_top_authors(self):
        """
        Obtiene los autores más destacados de Ecuador
        
        Returns:
            list: Lista de autores destacados
        """
        print("Identificando autores destacados de Ecuador...")
        
        params_authors = {
            'filter': 'last_known_institution.country_code:EC',
            'sort': 'works_count:desc',
            'per_page': 50
        }
        
        results_authors = self.query_api('authors', params_authors)
        if results_authors and 'results' in results_authors:
            top_authors = []
            for author in results_authors['results'][:20]:  # Tomar los 20 primeros
                author_data = {
                    'id': author.get('id'),
                    'nombre': author.get('display_name'),
                    'orcid': author.get('orcid'),
                    'institucion': author.get('last_known_institution', {}).get('display_name', 'Desconocida'),
                    'institucion_id': author.get('last_known_institution', {}).get('id', ''),
                    'publicaciones_total': author.get('works_count', 0),
                    'citas': author.get('cited_by_count', 0)
                }
                top_authors.append(author_data)
                print(f"  - {author_data['nombre']} ({author_data['institucion']}): {author_data['publicaciones_total']} publicaciones, {author_data['citas']} citas")
            
            # Guardar datos de autores destacados
            with open(os.path.join(DATA_DIR, 'autores_destacados.json'), 'w') as f:
                json.dump(top_authors, f, indent=2)
            
            # Crear visualizaciones
            self.visualize_top_authors(top_authors)
            
            return top_authors
        
        return []
    
    def get_top_institutions(self):
        """
        Obtiene las instituciones más destacadas de Ecuador
        
        Returns:
            list: Lista de instituciones destacadas
        """
        print("Identificando instituciones destacadas de Ecuador...")
        
        params_institutions = {
            'filter': 'country_code:EC',
            'sort': 'works_count:desc',
            'per_page': 25
        }
        
        results_institutions = self.query_api('institutions', params_institutions)
        if results_institutions and 'results' in results_institutions:
            top_institutions = []
            for inst in results_institutions['results'][:15]:  # Tomar las 15 primeras
                inst_data = {
                    'id': inst.get('id'),
                    'nombre': inst.get('display_name'),
                    'tipo': inst.get('type'),
                    'publicaciones': inst.get('works_count', 0),
                    'citas': inst.get('cited_by_count', 0)
                }
                top_institutions.append(inst_data)
                print(f"  - {inst_data['nombre']}: {inst_data['publicaciones']} publicaciones, {inst_data['citas']} citas")
            
            # Guardar datos de instituciones destacadas
            with open(os.path.join(DATA_DIR, 'instituciones_destacadas.json'), 'w') as f:
                json.dump(top_institutions, f, indent=2)
            
            # Crear visualizaciones
            self.visualize_top_institutions(top_institutions)
            
            return top_institutions
        
        return []
    
    def get_international_collaboration(self):
        """
        Analiza la colaboración internacional de Ecuador
        
        Returns:
            dict: Datos de colaboración internacional
        """
        print("Analizando colaboración internacional...")
        
        params_collab = {
            'filter': f'authorships.institutions.country_code:EC,publication_year:{self.period}',
            'group_by': 'authorships.countries'
        }
        
        results_collab = self.query_api('works', params_collab)
        if results_collab and 'group_by' in results_collab:
            collab_data = {}
            for item in results_collab['group_by']:
                country = item['key']
                if country != 'EC':  # Excluir Ecuador de la lista de colaboraciones
                    count = item['count']
                    percentage = (count / self.total_publications) * 100
                    collab_data[country] = {
                        'count': count,
                        'percentage': percentage
                    }
                    print(f"  - {country}: {count} publicaciones ({percentage:.2f}%)")
            
            # Guardar datos de colaboración internacional
            with open(os.path.join(DATA_DIR, 'colaboracion_internacional.json'), 'w') as f:
                json.dump(collab_data, f, indent=2)
            
            # Crear visualizaciones
            self.visualize_international_collaboration(collab_data)
            
            return collab_data
        
        return {}
    
    def visualize_oa_types(self, oa_types_data):
        """
        Crea visualización de tipos de acceso abierto
        
        Args:
            oa_types_data (dict): Datos de tipos de acceso abierto
        """
        # Preparar datos para el gráfico
        labels = list(oa_types_data.keys())
        sizes = [data['count'] for data in oa_types_data.values()]
        
        # Definir colores para cada tipo de OA
        colors = {
            'gold': CEDIA_COLORS['orange'],
            'hybrid': CEDIA_COLORS['turquoise'],
            'diamond': CEDIA_COLORS['green'],
            'green': CEDIA_COLORS['light_blue'],
            'bronze': '#CD7F32',
            'closed': CEDIA_COLORS['dark_blue']
        }
        
        # Asignar colores a cada segmento
        pie_colors = [colors.get(label, '#CCCCCC') for label in labels]
        
        # Crear gráfico de pastel
        plt.figure(figsize=(10, 8))
        wedges, texts, autotexts = plt.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=pie_colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        
        # Personalizar textos
        for text in texts:
            text.set_color(CEDIA_COLORS['dark_blue'])
            text.set_fontsize(12)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        plt.axis('equal')
        plt.title('Distribución de publicaciones ecuatorianas por tipo de acceso', 
                fontsize=16, color=CEDIA_COLORS['dark_blue'], pad=20)
        
        # Añadir leyenda explicativa
        legend_labels = {
            'gold': 'Gold: Publicado en revista de acceso abierto con APC',
            'hybrid': 'Hybrid: Publicado en revista de suscripción con opción OA',
            'diamond': 'Diamond: Publicado en revista de acceso abierto sin APC',
            'green': 'Green: Versión de autor disponible en repositorio',
            'bronze': 'Bronze: Disponible en web de editor sin licencia clara',
            'closed': 'Closed: Acceso restringido por suscripción'
        }
        
        custom_lines = [plt.Line2D([0], [0], color=colors[key], lw=4) for key in legend_labels.keys() if key in labels]
        custom_labels = [legend_labels[key] for key in legend_labels.keys() if key in labels]
        
        plt.legend(custom_lines, custom_labels, loc='lower center', bbox_to_anchor=(0.5, -0.15), 
                  ncol=2, fontsize=10, frameon=True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'distribucion_tipos_oa.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de distribución de tipos de OA guardado.")
    
    def visualize_fields_data(self, fields_data):
        """
        Crea visualizaciones de datos por áreas de conocimiento
        
        Args:
            fields_data (dict): Datos por áreas de conocimiento
        """
        # Convertir a DataFrame para facilitar la visualización
        areas_list = []
        for field_id, data in fields_data.items():
            area_info = {
                'id': field_id,
                'nombre': data['nombre'],
                'publicaciones': data['publicaciones'],
                'porcentaje': data['porcentaje']
            }
            
            # Añadir datos de OA si existen
            if 'porcentaje_oa' in data:
                area_info['porcentaje_oa'] = data['porcentaje_oa']
            
            # Añadir distribución por tipo de OA si existe
            if 'oa_status' in data:
                for oa_type, oa_info in data['oa_status'].items():
                    area_info[f'oa_{oa_type}'] = oa_info['percentage']
            
            areas_list.append(area_info)
        
        df_areas = pd.DataFrame(areas_list)
        
        # Ordenar por número de publicaciones
        df_areas = df_areas.sort_values('publicaciones', ascending=False)
        
        # 1. Gráfico de barras de las principales áreas de conocimiento
        top_areas = df_areas.head(10)
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(top_areas['nombre'], top_areas['publicaciones'], color=CEDIA_COLORS['turquoise'])
        plt.xlabel('Número de publicaciones')
        plt.ylabel('Área de conocimiento')
        plt.title('Principales áreas de conocimiento en publicaciones ecuatorianas', fontsize=14, color=CEDIA_COLORS['dark_blue'])
        
        # Añadir etiquetas de datos
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 50, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                    ha='left', va='center', color=CEDIA_COLORS['dark_blue'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'areas_conocimiento_principales.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de principales áreas de conocimiento guardado.")
        
        # 2. Gráfico de porcentaje de acceso abierto por área
        if 'porcentaje_oa' in df_areas.columns:
            top_areas_oa = df_areas.sort_values('porcentaje_oa', ascending=False).head(10)
            
            plt.figure(figsize=(12, 8))
            bars = plt.barh(top_areas_oa['nombre'], top_areas_oa['porcentaje_oa'], color=CEDIA_COLORS['green'])
            plt.xlabel('Porcentaje de publicaciones en acceso abierto (%)')
            plt.ylabel('Área de conocimiento')
            plt.title('Áreas con mayor porcentaje de publicaciones en acceso abierto', fontsize=14, color=CEDIA_COLORS['dark_blue'])
            plt.xlim(0, 100)
            
            # Añadir etiquetas de datos
            for bar in bars:
                width = bar.get_width()
                plt.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                        ha='left', va='center', color=CEDIA_COLORS['dark_blue'])
            
            plt.tight_layout()
            plt.savefig(os.path.join(VIZ_DIR, 'areas_mayor_acceso_abierto.png'), dpi=300, bbox_inches='tight')
            print("Gráfico de áreas con mayor acceso abierto guardado.")
        
        # 3. Gráfico de pastel con la distribución general de áreas
        plt.figure(figsize=(12, 12))
        
        # Tomar las 8 principales áreas y agrupar el resto
        if len(df_areas) > 8:
            top_areas_pie = df_areas.head(8)
            other_areas = pd.DataFrame([{
                'nombre': 'Otras áreas',
                'publicaciones': df_areas.iloc[8:]['publicaciones'].sum(),
                'porcentaje': df_areas.iloc[8:]['porcentaje'].sum()
            }])
            pie_data = pd.concat([top_areas_pie, other_areas])
        else:
            pie_data = df_areas
        
        # Crear paleta de colores basada en los colores de CEDIA
        colors = [CEDIA_COLORS['turquoise'], CEDIA_COLORS['dark_blue'], CEDIA_COLORS['medium_blue'], 
                CEDIA_COLORS['light_blue'], CEDIA_COLORS['green'], CEDIA_COLORS['orange'],
                '#3159AB', '#B9E1E2', '#F7D3B5']
        
        plt.pie(pie_data['publicaciones'], labels=pie_data['nombre'], autopct='%1.1f%%', 
                startangle=90, colors=colors[:len(pie_data)], wedgeprops={'edgecolor': 'w', 'linewidth': 1})
        
        plt.axis('equal')
        plt.title('Distribución de publicaciones ecuatorianas por área de conocimiento', 
                fontsize=16, color=CEDIA_COLORS['dark_blue'], pad=20)
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'distribucion_areas_conocimiento.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de distribución general de áreas guardado.")
    
    def visualize_top_authors(self, top_authors):
        """
        Crea visualizaciones de autores destacados
        
        Args:
            top_authors (list): Lista de autores destacados
        """
        # Convertir a DataFrame para facilitar la visualización
        df_authors = pd.DataFrame(top_authors)
        
        # Ordenar por número de publicaciones
        df_authors = df_authors.sort_values('publicaciones_total', ascending=False).head(15)
        
        # Crear gráfico de barras para autores destacados por publicaciones
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df_authors['nombre'], df_authors['publicaciones_total'], color=CEDIA_COLORS['turquoise'])
        plt.xlabel('Número de publicaciones')
        plt.ylabel('Autor')
        plt.title('Autores ecuatorianos más productivos', fontsize=14, color=CEDIA_COLORS['dark_blue'])
        
        # Añadir etiquetas de datos
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 5, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                    ha='left', va='center', color=CEDIA_COLORS['dark_blue'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'autores_mas_productivos.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de autores más productivos guardado.")
        
        # Crear gráfico de barras para autores destacados por citas
        df_authors_citas = df_authors.sort_values('citas', ascending=False).head(15)
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df_authors_citas['nombre'], df_authors_citas['citas'], color=CEDIA_COLORS['medium_blue'])
        plt.xlabel('Número de citas')
        plt.ylabel('Autor')
        plt.title('Autores ecuatorianos más citados', fontsize=14, color=CEDIA_COLORS['dark_blue'])
        
        # Añadir etiquetas de datos
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 5, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                    ha='left', va='center', color=CEDIA_COLORS['dark_blue'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'autores_mas_citados.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de autores más citados guardado.")
        
        # Crear gráfico de dispersión de publicaciones vs citas
        plt.figure(figsize=(10, 8))
        plt.scatter(df_authors['publicaciones_total'], df_authors['citas'], 
                alpha=0.7, s=100, c=[CEDIA_COLORS['turquoise']])
        
        # Añadir etiquetas para algunos autores destacados
        for i, row in df_authors.iterrows():
            if row['citas'] > df_authors['citas'].median() or row['publicaciones_total'] > df_authors['publicaciones_total'].median():
                plt.annotate(row['nombre'], 
                            (row['publicaciones_total'], row['citas']),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, color=CEDIA_COLORS['dark_blue'])
        
        plt.xlabel('Número de publicaciones')
        plt.ylabel('Número de citas')
        plt.title('Relación entre productividad e impacto de autores ecuatorianos', fontsize=14, color=CEDIA_COLORS['dark_blue'])
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'productividad_vs_impacto.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de productividad vs impacto guardado.")
    
    def visualize_top_institutions(self, top_institutions):
        """
        Crea visualizaciones de instituciones destacadas
        
        Args:
            top_institutions (list): Lista de instituciones destacadas
        """
        # Convertir a DataFrame
        df_institutions = pd.DataFrame(top_institutions)
        
        # Ordenar por número de publicaciones
        df_institutions = df_institutions.sort_values('publicaciones', ascending=False).head(10)
        
        # Crear gráfico de barras para instituciones por publicaciones
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df_institutions['nombre'], df_institutions['publicaciones'], color=CEDIA_COLORS['green'])
        plt.xlabel('Número de publicaciones')
        plt.ylabel('Institución')
        plt.title('Instituciones ecuatorianas más productivas', fontsize=14, color=CEDIA_COLORS['dark_blue'])
        
        # Añadir etiquetas de datos
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 50, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                    ha='left', va='center', color=CEDIA_COLORS['dark_blue'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'instituciones_mas_productivas.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de instituciones más productivas guardado.")
    
    def visualize_international_collaboration(self, collab_data):
        """
        Crea visualizaciones de colaboración internacional
        
        Args:
            collab_data (dict): Datos de colaboración internacional
        """
        # Convertir a DataFrame
        collab_list = []
        for country, data in collab_data.items():
            collab_list.append({
                'pais': country.replace('https://openalex.org/countries/', ''),
                'publicaciones': data['count'],
                'porcentaje': data['percentage']
            })
        
        df_collab = pd.DataFrame(collab_list)
        
        # Ordenar por número de publicaciones
        df_collab = df_collab.sort_values('publicaciones', ascending=False).head(15)
        
        # Crear gráfico de barras para colaboración internacional
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df_collab['pais'], df_collab['publicaciones'], color=CEDIA_COLORS['orange'])
        plt.xlabel('Número de publicaciones en colaboración')
        plt.ylabel('País')
        plt.title('Principales países colaboradores con Ecuador', fontsize=14, color=CEDIA_COLORS['dark_blue'])
        
        # Añadir etiquetas de datos
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 50, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
                    ha='left', va='center', color=CEDIA_COLORS['dark_blue'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, 'colaboracion_internacional.png'), dpi=300, bbox_inches='tight')
        print("Gráfico de colaboración internacional guardado.")
    
    def create_summary_analysis(self):
        """
        Crea un análisis resumido de todos los datos para la web
        
        Returns:
            dict: Análisis resumido
        """
        print("Creando análisis resumido para la web...")
        
        # Cargar datos de autores destacados
        try:
            with open(os.path.join(DATA_DIR, 'autores_destacados.json'), 'r') as f:
                top_authors = json.load(f)
            df_authors = pd.DataFrame(top_authors)
            df_authors_citas = df_authors.sort_values('citas', ascending=False)
        except:
            top_authors = []
            df_authors = pd.DataFrame()
            df_authors_citas = pd.DataFrame()
        
        # Cargar datos de instituciones destacadas
        try:
            with open(os.path.join(DATA_DIR, 'instituciones_destacadas.json'), 'r') as f:
                top_institutions = json.load(f)
            df_institutions = pd.DataFrame(top_institutions)
        except:
            top_institutions = []
            df_institutions = pd.DataFrame()
        
        # Cargar datos de colaboración internacional
        try:
            with open(os.path.join(DATA_DIR, 'colaboracion_internacional.json'), 'r') as f:
                collab_data = json.load(f)
            
            collab_list = []
            for country, data in collab_data.items():
                collab_list.append({
                    'pais': country.replace('https://openalex.org/countries/', ''),
                    'publicaciones': data['count'],
                    'porcentaje': data['percentage']
                })
            df_collab = pd.DataFrame(collab_list)
        except:
            collab_data = {}
            df_collab = pd.DataFrame()
        
        # Crear análisis resumido
        analysis_results = {
            'autores_destacados': {
                'total_analizados': len(top_authors),
                'mas_productivos': df_authors[['nombre', 'institucion', 'publicaciones_total']].to_dict('records') if not df_authors.empty else [],
                'mas_citados': df_authors_citas[['nombre', 'institucion', 'citas']].to_dict('records') if not df_authors_citas.empty else []
            },
            'instituciones_destacadas': {
                'total_analizadas': len(top_institutions),
                'mas_productivas': df_institutions[['nombre', 'publicaciones', 'citas']].to_dict('records') if not df_institutions.empty else []
            },
            'colaboracion_internacional': {
                'total_paises': len(collab_data),
                'principales_colaboradores': df_collab[['pais', 'publicaciones', 'porcentaje']].to_dict('records') if not df_collab.empty else []
            }
        }
        
        # Guardar análisis resumido
        with open(os.path.join(DATA_DIR, 'analisis_resumido.json'), 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        print("Análisis resumido guardado.")
        return analysis_results
    
    def run_full_analysis(self):
        """
        Ejecuta el análisis completo de datos
        """
        print(f"Iniciando análisis completo de publicaciones científicas ecuatorianas ({self.period})...")
        
        # 1. Obtener estadísticas generales
        self.get_general_stats()
        
        # 2. Obtener estadísticas de acceso abierto
        self.get_oa_stats()
        
        # 3. Obtener datos por áreas de conocimiento
        self.get_data_by_field()
        
        # 4. Obtener autores destacados
        self.get_top_authors()
        
        # 5. Obtener instituciones destacadas
        self.get_top_institutions()
        
        # 6. Analizar colaboración internacional
        self.get_international_collaboration()
        
        # 7. Crear análisis resumido
        self.create_summary_analysis()
        
        print("Análisis completo finalizado.")
        print(f"Datos guardados en: {DATA_DIR}")
        print(f"Visualizaciones guardadas en: {VIZ_DIR}")


# Ejemplo de uso
if __name__ == "__main__":
    extractor = OpenAlexExtractor()
    extractor.run_full_analysis()
